#!/usr/bin/env python3
"""Generate a node table for `svr4-ufs-populate --device-table`.

Ports the device-assignment logic from the old `tasks/make_image.py`: it derives
the `/dev` node major/minor numbers from the kernel reconfiguration tree
(`cf.d/conf.c`, `mdevice.d/*`, `node.d/*`) — the same metadata that ships in
the sysroot's `/etc/conf` so a booted system can relink its kernel — and emits
the runtime directories, device nodes, and the `/dev/systty` link the root
filesystem needs.

The output is the line format `svr4-ufs-populate` consumes:

    /path d <octal-mode>            # directory (created or chmod'd)
    /path c|b <major> <minor> <mode># char / block device node
    /path l <target>               # hard link

Stdlib only — the build can run this with the host `python3` and no packages.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Directories the running system needs that are not (reliably) in the package
# tree, with the modes they must end up with (notably the sticky /tmp dirs).
RUNTIME_DIRECTORIES: dict[str, int] = {
    "/root": 0o755,
    "/tmp": 0o1777,
    "/tmp/.X11-unix": 0o1777,
    "/var": 0o755,
    "/var/lib": 0o755,
    "/var/lib/xkb": 0o755,
    "/var/log": 0o755,
}

# (type, major, minor): type is "c" (char) or "b" (block). Overridden below from
# the kernel conf where the real majors are discoverable.
DEFAULT_DEVICE_ASSIGNMENTS: dict[str, tuple[str, int, int]] = {
    "/dev/console": ("c", 30, 0),
    "/dev/syscon": ("c", 30, 0),
    "/dev/tty": ("c", 16, 0),
    "/dev/vt00": ("c", 5, 0),
    "/dev/vtmon": ("c", 30, 15),
    "/dev/video": ("c", 29, 0),
    "/dev/vidadm": ("c", 29, 1),
    "/dev/kd/kd00": ("c", 30, 0),
    "/dev/kd/kdvm00": ("c", 20, 0),
    "/dev/sad/admin": ("c", 25, 1),
    "/dev/sad/user": ("c", 25, 0),
    "/dev/root": ("b", 0, 1),
    "/dev/pipe": ("b", 0, 1),
    "/dev/swap": ("b", 0, 2),
    "/dev/dump": ("b", 0, 2),
    "/dev/null": ("c", 2, 2),
    "/dev/sysmsg": ("c", 19, 0),
    "/dev/zero": ("c", 2, 4),
    "/dev/urandom": ("c", 2, 5),
}

NETWORK_NODE_MODULES = (
    "arp", "icmp", "ip", "llcloop", "rawip",
    "tcp", "ticlts", "ticots", "ticotsor", "udp",
)

DEVICE_MODE = 0o600


def _conf_file(conf_root: Path, rel: str) -> Path | None:
    candidate = conf_root / rel
    return candidate if candidate.is_file() else None


def _parse_number(token: str) -> int:
    try:
        return int(token, 0)
    except ValueError:
        return int(token, 16)


def _iter_metadata_lines(path: Path) -> list[str]:
    lines = []
    for raw in path.read_text().splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("*") or stripped.startswith("#"):
            continue
        lines.append(stripped)
    return lines


def _load_character_majors(conf_root: Path) -> dict[str, int]:
    conf_c = _conf_file(conf_root, "cf.d/conf.c")
    if conf_c is None:
        return {}
    majors: dict[str, int] = {}
    text = conf_c.read_text()
    match = re.search(
        r"struct\s+cdevsw\s+cdevsw\[\]\s*=\s*\{(?P<body>.*?)^\};",
        text,
        flags=re.MULTILINE | re.DOTALL,
    )
    if match is None:
        return majors
    for line in match.group("body").splitlines():
        entry = re.search(r'/\*\s*(?P<major>\d+)\s*\*/.*"(?P<name>[^"]+)"', line)
        if entry is None:
            continue
        name = entry.group("name")
        if name == "nodev":
            continue
        majors[name] = int(entry.group("major"))
    return majors


def _parse_node_minor(token: str, character_majors: dict[str, int]) -> int:
    if token in character_majors:
        return character_majors[token]
    if re.fullmatch(r"0[0-7]+", token):
        return int(token, 8)
    return _parse_number(token)


def _load_network_assignments(conf_root: Path) -> dict[str, tuple[str, int, int]]:
    character_majors = _load_character_majors(conf_root)
    node_dir = conf_root / "node.d"
    assignments: dict[str, tuple[str, int, int]] = {}
    if not character_majors or not node_dir.is_dir():
        return assignments
    for module_name in NETWORK_NODE_MODULES:
        node_path = node_dir / module_name
        if not node_path.is_file():
            continue
        for line in _iter_metadata_lines(node_path):
            fields = line.split()
            if len(fields) < 4:
                continue
            device_name, relative_path, node_type, minor_token = fields[:4]
            if not node_type.startswith("c"):
                continue
            major = character_majors.get(device_name)
            if major is None:
                continue
            try:
                minor = _parse_node_minor(minor_token, character_majors)
            except ValueError:
                continue
            assignments[f"/dev/{relative_path}"] = ("c", major, minor)
    return assignments


def _first_record_major(conf_root: Path, module: str) -> int | None:
    """Return field[5] (the major) of the first `mdevice.d/<module>` record."""
    path = _conf_file(conf_root, f"mdevice.d/{module}")
    if path is None:
        return None
    for line in path.read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("*") or stripped.startswith("#"):
            continue
        fields = stripped.split()
        if len(fields) < 6 or fields[0] != module:
            return None
        return int(fields[5], 0)
    return None


def load_device_assignments(conf_root: Path) -> dict[str, tuple[str, int, int]]:
    assignments = dict(DEFAULT_DEVICE_ASSIGNMENTS)

    # rootdev/pipedev/swapdev/dumpdev come from cf.d/conf.c makedevice() calls.
    conf_c = _conf_file(conf_root, "cf.d/conf.c")
    if conf_c is not None:
        pattern = re.compile(
            r"dev_t\s+(rootdev|pipedev|swapdev|dumpdev)\s*=\s*makedevice\((\d+),\s*(\d+)\);"
        )
        mapping = {
            "rootdev": "/dev/root",
            "pipedev": "/dev/pipe",
            "swapdev": "/dev/swap",
            "dumpdev": "/dev/dump",
        }
        for match in pattern.finditer(conf_c.read_text()):
            path = mapping[match.group(1)]
            file_type = assignments[path][0]
            assignments[path] = (file_type, int(match.group(2)), int(match.group(3)))

    # Per-driver majors from the mdevice.d fragments.
    sysmsg = _first_record_major(conf_root, "sysmsg")
    if sysmsg is not None:
        assignments["/dev/sysmsg"] = ("c", sysmsg, 0)

    mem = _first_record_major(conf_root, "mem")
    if mem is not None:
        assignments["/dev/null"] = ("c", mem, 2)
        assignments["/dev/zero"] = ("c", mem, 4)
        assignments["/dev/urandom"] = ("c", mem, 5)

    cmux = _first_record_major(conf_root, "cmux")
    if cmux is not None:
        assignments["/dev/vt00"] = ("c", cmux, 0)

    kd = _first_record_major(conf_root, "kd")
    if kd is not None:
        assignments["/dev/console"] = ("c", kd, 0)
        assignments["/dev/syscon"] = ("c", kd, 0)
        assignments["/dev/vtmon"] = ("c", kd, 15)
        assignments["/dev/kd/kd00"] = ("c", kd, 0)
        assignments["/dev/kd/kd01"] = ("c", kd, 1)

    kdvm = _first_record_major(conf_root, "kdvm")
    if kdvm is not None:
        assignments["/dev/kd/kdvm00"] = ("c", kdvm, 0)
        assignments["/dev/kd/kdvm01"] = ("c", kdvm, 1)

    gvid = _first_record_major(conf_root, "gvid")
    if gvid is not None:
        assignments["/dev/video"] = ("c", gvid, 0)
        assignments["/dev/vidadm"] = ("c", gvid, 1)

    m320 = _first_record_major(conf_root, "m320")
    if m320 is not None:
        assignments["/dev/mouse"] = ("c", m320, 0)

    sad = _first_record_major(conf_root, "sad")
    if sad is not None:
        assignments["/dev/sad/user"] = ("c", sad, 0)
        assignments["/dev/sad/admin"] = ("c", sad, 1)

    assignments.update(_load_network_assignments(conf_root))

    # Pseudo-terminals.
    character_majors = _load_character_majors(conf_root)
    clone_major = character_majors.get("clone", 4)
    ptm_major = character_majors.get("ptm", 11)
    pts_major = character_majors.get("pts", 35)
    assignments["/dev/ptmx"] = ("c", clone_major, ptm_major)
    for i in range(32):
        assignments[f"/dev/pts/{i}"] = ("c", pts_major, i)

    return assignments


def emit(conf_root: Path, out) -> None:
    assignments = load_device_assignments(conf_root)

    out.write("# Generated by gen-device-table.py — do not edit.\n")
    out.write("# Consumed by svr4-ufs-populate --device-table.\n\n")

    # 1. Runtime directories (sorted shallow-first so parents precede children).
    out.write("# runtime directories\n")
    for path in sorted(RUNTIME_DIRECTORIES, key=lambda p: (p.count("/"), p)):
        out.write(f"{path} d 0{RUNTIME_DIRECTORIES[path]:o}\n")
    out.write("\n")

    # 2. Device nodes (sorted shallow-first so /dev/kd exists before /dev/kd/kd00;
    #    svr4-ufs-populate also auto-creates any missing parent as 0755).
    out.write("# device nodes\n")
    for path in sorted(assignments, key=lambda p: (p.count("/"), p)):
        file_type, major, minor = assignments[path]
        out.write(f"{path} {file_type} {major} {minor} 0{DEVICE_MODE:o}\n")
    out.write("\n")

    # 3. Links (targets must already exist above).
    out.write("# links\n")
    if "/dev/syscon" in assignments:
        out.write("/dev/systty l /dev/syscon\n")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--kernel-conf",
        required=True,
        type=Path,
        help="Kernel reconfiguration tree (the sysroot's /etc/conf, with cf.d/, "
        "mdevice.d/, node.d/).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Write the table here (default: stdout).",
    )
    args = parser.parse_args(argv)

    if not args.kernel_conf.is_dir():
        parser.error(f"kernel-conf {args.kernel_conf} is not a directory")

    if args.output is None:
        emit(args.kernel_conf, sys.stdout)
    else:
        with args.output.open("w") as handle:
            emit(args.kernel_conf, handle)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
