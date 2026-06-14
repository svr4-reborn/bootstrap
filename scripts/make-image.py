#!/usr/bin/env python3
"""Build the SVR4 hard-disk image with rsync over the UFS FUSE driver.

This is the rsync-based replacement for the `svr4-ufs-populate` path: rather than
walking the sysroot in-process and writing through the UFS library, it mounts each
filesystem slice with its FUSE driver and `rsync`s the sysroot in. The win is that
rsync handles the tree copy (ownership, perms, hard links, deletions of stale
files) and the driver is exercised exactly as a real mount would be.

The slice-specific knowledge lives behind the `SliceBuilder` abstraction, so the
filesystem used for a slice can be changed by swapping in a different builder —
the orchestration (`build_image`) does not care whether a slice is UFS, BFS, or
something else. Today:

  * `UfsFuseSlice`  — the root slice: format UFS, FUSE-mount, rsync the sysroot
                      in, then apply the device-node table (the kernel `/dev`
                      nodes rsync cannot carry) through the mount with `mknod`.
  * `BfsFromDir`    — the `/stand` slice: rebuilt wholesale from `sysroot/stand`
                      via `svr4-disk-image format-bfs --from-dir`. BFS is flat and
                      tiny, so there is nothing to gain from a mount + rsync.

Everything calls out to the `svr4-disk-image` / `svr4-ufs-mount` host tools (built
by the `host-svr4-ufs` xbstrap tool) and to `rsync` / `fusermount`. Only the
Python standard library is imported, so the build can run this with the host
`python3` and no extra packages.

Root is required only for a *full build* — one that (re)formats the root slice
and recreates the kernel `/dev` nodes. Those nodes go in through `mknod(2)`
against the mounted tree, and the host kernel blocks that for unprivileged users
(`CAP_MKNOD`) before the request reaches the FUSE driver. Needing root there is
the same trade-off other hobby-OS distributions make (e.g. managarm, whose
loopback-mount paths require it), so we lean into it rather than working around it.

When the image already exists and its `/dev` nodes already match the device table
(tracked by a hash sidecar — see below), the build is a *refresh*: the userland is
rsync'd into the existing image and the device-node pass is skipped, so it runs
unprivileged. This is the fast path for iterating on userland changes.
"""

from __future__ import annotations

import argparse
import dataclasses
import os
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Iterable, Sequence


# ---------------------------------------------------------------------------
# Small subprocess helpers.
# ---------------------------------------------------------------------------


def _run(command: Sequence[str], *, cwd: Path | None = None) -> None:
    """Run a command, raising SystemExit with its name on failure."""
    printable = " ".join(str(c) for c in command)
    print(f"+ {printable}", flush=True)
    try:
        subprocess.run([str(c) for c in command], cwd=cwd, check=True)
    except FileNotFoundError as error:
        raise SystemExit(f"error: {command[0]} not found on PATH") from error
    except subprocess.CalledProcessError as error:
        raise SystemExit(
            f"error: {command[0]} failed with exit status {error.returncode}"
        ) from error


def _wait_ignoring_sigint(process: subprocess.Popen, *, timeout: float) -> int:
    """Wait for `process`, ignoring SIGINT meanwhile so Ctrl-C during a long
    rsync/unmount tears the child down cleanly instead of orphaning the mount."""
    previous = signal.getsignal(signal.SIGINT)
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    try:
        return process.wait(timeout=timeout)
    finally:
        signal.signal(signal.SIGINT, previous)


def _is_mounted(path: Path) -> bool:
    if os.path.ismount(path):
        return True
    if shutil.which("findmnt") is None:
        return False
    result = subprocess.run(
        ["findmnt", "--mountpoint", str(path)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.returncode == 0


# ---------------------------------------------------------------------------
# Tool locations. The host-svr4-ufs xbstrap tool installs these into the tool
# prefix, which is on PATH when this runs as a task; we resolve them up front so
# a missing tool fails with a clear message.
# ---------------------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class Tools:
    disk_image: str
    ufs_mount: str
    rsync: str

    @classmethod
    def discover(cls) -> "Tools":
        def need(name: str) -> str:
            found = shutil.which(name)
            if found is None:
                raise SystemExit(
                    f"error: required tool {name!r} not found on PATH "
                    "(is the host-svr4-ufs tool installed?)"
                )
            return found

        return cls(
            disk_image=need("svr4-disk-image"),
            ufs_mount=need("svr4-ufs-mount"),
            rsync=need("rsync"),
        )


# ---------------------------------------------------------------------------
# rsync.
# ---------------------------------------------------------------------------

# -aH preserves perms/times/symlinks and hard links; --numeric-ids keeps the
# sysroot's root:root ownership without name lookups; --delete prunes files that
# left the sysroot so a reused image tracks it exactly; --inplace/--whole-file
# avoid temp files and rolling-checksum work the FUSE driver gains nothing from.
_RSYNC_COMMON = (
    "-aH",
    "--numeric-ids",
    "--delete",
    "--inplace",
    "--whole-file",
    # TODO: --checksum is needed since otherwise rsync will not always actually notice stuff.
    #  Clanker thinks this is a mtime-coarseness issue, but I've done stuff that is so far away from that and it still doesnt notice.
    "--checksum",
    "--human-readable",
    "--info=progress2,stats2",
)


def rsync_tree(
    tools: Tools,
    source: Path,
    dest: Path,
    *,
    excludes: Iterable[str] = (),
) -> None:
    """rsync the *contents* of `source` into `dest` (trailing slashes matter)."""
    command = [tools.rsync, *_RSYNC_COMMON]
    command.extend(f"--exclude={pattern}" for pattern in excludes)
    command.append(f"{source}/")
    command.append(f"{dest}/")
    _run(command)


# ---------------------------------------------------------------------------
# FUSE mount context manager.
# ---------------------------------------------------------------------------


class FuseMount:
    """Mount a UFS slice with `svr4-ufs-mount` for the duration of a `with`
    block, unmounting (robustly) on exit. Ported from the old make_image.py."""

    def __init__(self, tools: Tools, image: Path, slice_selector: str):
        self._tools = tools
        self._image = image
        self._slice = slice_selector
        self._process: subprocess.Popen | None = None
        self._tmpdir: tempfile.TemporaryDirectory | None = None
        self.mountpoint: Path | None = None

    def __enter__(self) -> Path:
        self._tmpdir = tempfile.TemporaryDirectory(
            prefix=f"svr4-ufs-{self._slice}-", ignore_cleanup_errors=True
        )
        mountpoint = Path(self._tmpdir.name)
        self.mountpoint = mountpoint
        # We unmount the slice ourselves with `fusermount -u` (which drives the
        # driver's `destroy`, flushing a clean image); the fuser session then
        # drop-unmounts the already-detached mount and logs a benign EINVAL. Quiet
        # fuser's own mount/unmount chatter so that does not look like a failure,
        # while keeping the driver's own `svr4-ufs-mount` logs at info. An explicit
        # RUST_LOG from the caller wins.
        env = dict(os.environ)
        env.setdefault("RUST_LOG", "svr4_ufs_mount=info,fuser=error")
        self._process = subprocess.Popen(
            [
                self._tools.ufs_mount,
                str(self._image),
                str(mountpoint),
                "--slice",
                self._slice,
            ],
            start_new_session=True,
            env=env,
        )
        deadline = time.monotonic() + 10.0
        while time.monotonic() < deadline:
            if self._process.poll() is not None:
                raise SystemExit(
                    f"error: svr4-ufs-mount exited before mounting slice "
                    f"{self._slice!r}"
                )
            if _is_mounted(mountpoint):
                return mountpoint
            time.sleep(0.05)
        self._terminate()
        raise SystemExit(f"error: timed out mounting slice {self._slice!r}")

    def __exit__(self, *_exc) -> None:
        try:
            self._unmount()
        finally:
            if self._tmpdir is not None:
                self._tmpdir.cleanup()

    def _unmount(self) -> None:
        process = self._process
        mountpoint = self.mountpoint
        if process is None or mountpoint is None:
            return
        for unmount_command in (
            ["fusermount3", "-u", str(mountpoint)],
            ["fusermount", "-u", str(mountpoint)],
            ["fusermount3", "-uz", str(mountpoint)],
            ["fusermount", "-uz", str(mountpoint)],
        ):
            if shutil.which(unmount_command[0]) is None:
                continue
            subprocess.run(unmount_command, check=False)
            if process.poll() is not None or not _is_mounted(mountpoint):
                break
        self._terminate()

    def _terminate(self) -> None:
        process = self._process
        if process is None:
            return
        try:
            _wait_ignoring_sigint(process, timeout=5)
            return
        except subprocess.TimeoutExpired:
            pass
        for sig in (signal.SIGTERM, signal.SIGKILL):
            try:
                os.killpg(process.pid, sig)
            except ProcessLookupError:
                return
            try:
                _wait_ignoring_sigint(process, timeout=5)
                return
            except subprocess.TimeoutExpired:
                continue


# ---------------------------------------------------------------------------
# Device-node table. The format is what scripts/gen-device-table.py emits and
# svr4-ufs-populate consumes:
#
#   /path d <octal-mode>            directory (created or chmod'd)
#   /path c|b <major> <minor> [mode]  char / block device node
#   /path l <target>               hard link to an existing path
#
# `#` comments and blank lines are ignored. We replay it against a *mounted*
# tree with the ordinary syscalls (mkdir/mknod/link/chmod), so the same table
# drives both the direct-populate path and this rsync path.
# ---------------------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class DeviceTableEntry:
    path: str  # absolute, image-relative (leading '/')
    kind: str  # 'd', 'c', 'b', or 'l'
    fields: tuple[str, ...]


def parse_device_table(path: Path) -> list[DeviceTableEntry]:
    entries: list[DeviceTableEntry] = []
    for lineno, raw in enumerate(path.read_text().splitlines(), start=1):
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        parts = line.split()
        node_path, kind = parts[0], parts[1] if len(parts) > 1 else ""
        if kind not in ("d", "c", "b", "l"):
            raise SystemExit(
                f"error: {path}:{lineno}: type must be d, c, b, or l, got {kind!r}"
            )
        if not node_path.startswith("/"):
            raise SystemExit(
                f"error: {path}:{lineno}: device path {node_path!r} must be absolute"
            )
        entries.append(DeviceTableEntry(node_path, kind, tuple(parts[2:])))
    return entries


def _parse_int(token: str) -> int:
    return int(token, 16) if token.startswith("0x") else int(token, 10)


def apply_device_table(root: Path, entries: Sequence[DeviceTableEntry]) -> None:
    """Replay the device table against the mounted filesystem rooted at `root`.

    Parents are created 0755 as needed; this relies on the FUSE driver
    implementing `mknod` (char/block nodes only)."""
    saved_umask = os.umask(0)
    try:
        for entry in entries:
            target = root / entry.path.lstrip("/")
            target.parent.mkdir(parents=True, exist_ok=True)
            if entry.kind == "d":
                mode = int(entry.fields[0], 8)
                target.mkdir(exist_ok=True)
                target.chmod(mode)
            elif entry.kind in ("c", "b"):
                major = _parse_int(entry.fields[0])
                minor = _parse_int(entry.fields[1])
                mode = int(entry.fields[2], 8) if len(entry.fields) > 2 else 0o600
                fmt = stat.S_IFCHR if entry.kind == "c" else stat.S_IFBLK
                if target.exists():
                    target.unlink()
                os.mknod(target, mode | fmt, os.makedev(major, minor))
            elif entry.kind == "l":
                link_target = root / entry.fields[0].lstrip("/")
                if target.exists():
                    target.unlink()
                os.link(link_target, target)
    finally:
        os.umask(saved_umask)


def apply_device_table_directories(root: Path, entries: Sequence[DeviceTableEntry]) -> None:
    """Replay only directory entries from the device table.

    Refresh builds skip the full table because char/block device nodes need root,
    but directory modes such as sticky /tmp are ordinary chmods and should still
    track the generated table.
    """
    saved_umask = os.umask(0)
    try:
        for entry in entries:
            if entry.kind != "d":
                continue
            target = root / entry.path.lstrip("/")
            target.parent.mkdir(parents=True, exist_ok=True)
            mode = int(entry.fields[0], 8)
            target.mkdir(exist_ok=True)
            target.chmod(mode)
    finally:
        os.umask(saved_umask)


# ---------------------------------------------------------------------------
# Slice builders. Each knows how to format and populate one slice; the
# orchestrator just calls format() then populate(). Swap a builder to change the
# filesystem used for a slice.
# ---------------------------------------------------------------------------


class SliceBuilder:
    """A slice of the image: how to format it and how to fill it from the
    sysroot. Subclass to support a different filesystem for a slice."""

    selector: str

    def format(self, tools: Tools, image: Path, sysroot: Path) -> None:
        raise NotImplementedError

    def populate(
        self, tools: Tools, image: Path, sysroot: Path, *, apply_nodes: bool
    ) -> None:
        """Fill the slice from the sysroot. `apply_nodes` requests the device-node
        pass (root-only); a refresh of an unchanged image leaves it False."""
        raise NotImplementedError


class UfsFuseSlice(SliceBuilder):
    """Root slice on UFS: format, FUSE-mount, rsync the sysroot in (minus the
    paths owned by other slices), then apply the device-node table over the
    mount."""

    def __init__(
        self,
        selector: str,
        *,
        block_size: int,
        device_table: Path,
        rsync_excludes: Iterable[str] = (),
    ):
        self.selector = selector
        self._block_size = block_size
        self._device_table = device_table
        self._excludes = tuple(rsync_excludes)

    def format(self, tools: Tools, image: Path, sysroot: Path) -> None:
        _run(
            [
                tools.disk_image,
                "format-ufs",
                str(image),
                "--slice",
                self.selector,
                "--block-size",
                str(self._block_size),
            ]
        )

    def populate(
        self, tools: Tools, image: Path, sysroot: Path, *, apply_nodes: bool
    ) -> None:
        entries = parse_device_table(self._device_table)
        with FuseMount(tools, image, self.selector) as mountpoint:
            rsync_tree(tools, sysroot, mountpoint, excludes=self._excludes)
            if apply_nodes:
                apply_device_table(mountpoint, entries)
            else:
                apply_device_table_directories(mountpoint, entries)


class BfsFromDir(SliceBuilder):
    """`/stand` slice on BFS: rebuilt wholesale from a sysroot subdirectory via
    `svr4-disk-image format-bfs --from-dir`. BFS is flat and small, so there is
    no mount/rsync step — formatting from the directory *is* the population, and
    it is cheap and rootless, so it runs on every build (full or refresh) to pick
    up a rebuilt kernel."""

    def __init__(self, selector: str, *, from_subdir: str):
        self.selector = selector
        self._from_subdir = from_subdir

    def format(self, tools: Tools, image: Path, sysroot: Path) -> None:
        # The reformat-from-dir happens in populate() so it also runs on a
        # refresh; nothing extra to do here on a full build.
        pass

    def populate(
        self, tools: Tools, image: Path, sysroot: Path, *, apply_nodes: bool
    ) -> None:
        _run(
            [
                tools.disk_image,
                "format-bfs",
                str(image),
                "--slice",
                self.selector,
                "--from-dir",
                str(sysroot / self._from_subdir),
            ]
        )


# ---------------------------------------------------------------------------
# Orchestration.
# ---------------------------------------------------------------------------


def create_layout(tools: Tools, image: Path, size_mb: int) -> None:
    _run(
        [
            tools.disk_image,
            "create-layout",
            "--size",
            str(size_mb),
            "--output",
            str(image),
            "--disk-addressing",
            "lba28",
        ]
    )


def install_boot(tools: Tools, image: Path, sysroot: Path) -> None:
    _run(
        [
            tools.disk_image,
            "install-boot",
            str(image),
            "--hdboot",
            str(sysroot / "stand" / "hdboot"),
        ]
    )


# ---------------------------------------------------------------------------
# Device-node skip marker.
#
# The device table is a deterministic function of the kernel conf, so "are the
# /dev nodes already correct?" is decided by whether the table we are about to
# apply is byte-identical to the one last applied. We stamp a hash of the table
# into a sidecar next to the image after a successful node pass; a later run that
# sees the same hash (and an existing image) can refresh the userland with rsync
# alone — no device-node pass, and therefore no root. This is the agent-friendly
# fast path: edit userland, repopulate, run unprivileged.
#
# Reformatting the root UFS wipes /dev, so the node pass is bound to a full
# (re)build. A refresh deliberately skips the reformat as well as the nodes.
# ---------------------------------------------------------------------------

_MARKER_VERSION = "1"


def _device_marker_path(image: Path) -> Path:
    return image.with_name(image.name + ".devtab.sha256")


def _device_table_hash(device_table: Path) -> str:
    import hashlib

    digest = hashlib.sha256(device_table.read_bytes()).hexdigest()
    # Version-prefixed so a change to how nodes are applied can invalidate old
    # markers without a table change.
    return f"{_MARKER_VERSION}:{digest}"


def _device_nodes_current(image: Path, device_table: Path) -> bool:
    """True if `image` exists and its recorded device-table hash matches the
    table we would apply now — i.e. the device-node pass can be skipped."""
    marker = _device_marker_path(image)
    if not image.exists() or not marker.exists():
        return False
    try:
        return marker.read_text().strip() == _device_table_hash(device_table)
    except OSError:
        return False


def build_image(
    image: Path,
    sysroot: Path,
    *,
    size_mb: int,
    builders: Sequence[SliceBuilder],
    device_table: Path,
    create: bool,
) -> None:
    if not sysroot.is_dir():
        raise SystemExit(f"error: sysroot {sysroot} is not a directory")
    if not device_table.is_file():
        raise SystemExit(f"error: device table {device_table} does not exist")

    # A full (re)build reformats the slices and recreates /dev (root-only). A
    # refresh reuses an existing image whose device nodes already match the
    # table, rsync-ing the userland in unprivileged. --create forces the full
    # path. Decide this — and enforce the root requirement — before touching any
    # tools, so an unprivileged caller gets the actionable root message rather
    # than a confusing downstream failure.
    full_build = create or not _device_nodes_current(image, device_table)

    if full_build and os.geteuid() != 0:
        raise SystemExit(
            "error: a full image build must run as root — creating the /dev "
            "device nodes needs mknod(2), which the host kernel denies to "
            "unprivileged users (CAP_MKNOD). Re-run under sudo, or, to refresh "
            "userland into the existing image without touching /dev, leave the "
            f"image and its {_device_marker_path(image).name} marker in place."
        )

    tools = Tools.discover()

    if full_build:
        if create or not image.exists():
            create_layout(tools, image, size_mb)
        # Format reformats the slices so a rebuilt kernel/userland is picked up;
        # this also clears /dev, which the node pass below rebuilds.
        for builder in builders:
            builder.format(tools, image, sysroot)
    else:
        print(
            f"Refreshing {image.name} in place (device nodes unchanged; "
            "rsync only, no root needed)",
            flush=True,
        )

    for builder in builders:
        builder.populate(tools, image, sysroot, apply_nodes=full_build)

    if full_build:
        # Record the table we just applied so the next run can skip the node pass.
        _device_marker_path(image).write_text(_device_table_hash(device_table) + "\n")

    install_boot(tools, image, sysroot)
    print(f"Built SVR4 image at {image}", flush=True)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--image",
        type=Path,
        default=Path("hdd.img"),
        help="Output disk image (default: hdd.img in the working directory).",
    )
    parser.add_argument(
        "--sysroot",
        type=Path,
        default=Path("system-root"),
        help="Sysroot whose contents populate the image (default: system-root).",
    )
    parser.add_argument(
        "--device-table",
        type=Path,
        default=Path("devices.tab"),
        help="Device-node table from gen-device-table.py (default: devices.tab).",
    )
    parser.add_argument(
        "--size",
        type=int,
        default=4096,
        help="Disk image size in MiB, used only when creating the layout.",
    )
    parser.add_argument(
        "--block-size",
        type=int,
        default=4096,
        help="UFS block size for the root slice (default: 4096).",
    )
    parser.add_argument(
        "--create",
        action="store_true",
        help="Recreate the disk layout even if the image already exists.",
    )
    args = parser.parse_args(argv)

    # The standard SVR4 layout: a UFS root and a BFS /stand. To change the
    # filesystem used for a slice, swap the builder here.
    builders: list[SliceBuilder] = [
        UfsFuseSlice(
            "root",
            block_size=args.block_size,
            device_table=args.device_table,
            # /stand lives on its own BFS slice; keep it out of the root rsync.
            # /dev is owned by the device-node pass (apply_device_table), not the
            # sysroot.
            rsync_excludes=("/stand/***", "/dev/***"),
        ),
        BfsFromDir("stand", from_subdir="stand"),
    ]

    build_image(
        args.image.resolve(),
        args.sysroot.resolve(),
        size_mb=args.size,
        builders=builders,
        device_table=args.device_table.resolve(),
        create=args.create,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
