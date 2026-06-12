#!/usr/bin/env python3
import argparse
import fnmatch
import os
from pathlib import Path
import sys
import tarfile
import tempfile
import difflib


ALWAYS_EXCLUDES = [
    ".git",
    ".git/*",
    "*.xbstrap",
    "autom4te.cache",
    "autom4te.cache/*",
    ".autom4te.cache",
    ".autom4te.cache/*",
    "__pycache__",
    "__pycache__/*",
]

GENERATED_BUILD_SYSTEM_EXCLUDES = [
    "*~",
    "*.orig",
    "*.rej",
    ".deps",
    ".deps/*",
    "*/.deps",
    "*/.deps/*",
    "ABOUT-NLS",
    "Makefile.in",
    "*/Makefile.in",
    "aclocal.m4",
    "*/aclocal.m4",
    "ar-lib",
    "*/ar-lib",
    "compile",
    "*/compile",
    "config.guess",
    "*/config.guess",
    "config.h.in",
    "*/config.h.in",
    "config.rpath",
    "*/config.rpath",
    "config.sub",
    "*/config.sub",
    "configure",
    "*/configure",
    "depcomp",
    "*/depcomp",
    "install-sh",
    "*/install-sh",
    "ltmain.sh",
    "*/ltmain.sh",
    "mdate-sh",
    "*/mdate-sh",
    "missing",
    "*/missing",
    "mkinstalldirs",
    "*/mkinstalldirs",
    "test-driver",
    "*/test-driver",
    "texinfo.tex",
    "*/texinfo.tex",
    "ylwrap",
    "*/ylwrap",
    "build-aux/compile",
    "build-aux/config.guess",
    "build-aux/config.rpath",
    "build-aux/config.sub",
    "build-aux/depcomp",
    "build-aux/install-sh",
    "build-aux/ltmain.sh",
    "build-aux/missing",
    "build-aux/mkinstalldirs",
    "build-aux/test-driver",
    "m4/build-to-host.m4",
    "*/m4/build-to-host.m4",
    "m4/gettext.m4",
    "*/m4/gettext.m4",
    "m4/host-cpu-c-abi.m4",
    "*/m4/host-cpu-c-abi.m4",
    "m4/iconv.m4",
    "*/m4/iconv.m4",
    "m4/intlmacosx.m4",
    "*/m4/intlmacosx.m4",
    "m4/lib-ld.m4",
    "*/m4/lib-ld.m4",
    "m4/lib-link.m4",
    "*/m4/lib-link.m4",
    "m4/lib-prefix.m4",
    "*/m4/lib-prefix.m4",
    "m4/libtool.m4",
    "*/m4/libtool.m4",
    "m4/ltoptions.m4",
    "*/m4/ltoptions.m4",
    "m4/ltsugar.m4",
    "*/m4/ltsugar.m4",
    "m4/ltversion.m4",
    "*/m4/ltversion.m4",
    "m4/lt~obsolete.m4",
    "*/m4/lt~obsolete.m4",
    "m4/nls.m4",
    "*/m4/nls.m4",
    "m4/po.m4",
    "*/m4/po.m4",
    "m4/progtest.m4",
    "*/m4/progtest.m4",
    "po/Makefile.in.in",
    "*/po/Makefile.in.in",
    "po/Makevars.template",
    "*/po/Makevars.template",
    "po/Rules-quot",
    "*/po/Rules-quot",
    "po/boldquot.sed",
    "*/po/boldquot.sed",
    "po/en@boldquot.header",
    "*/po/en@boldquot.header",
    "po/en@quot.header",
    "*/po/en@quot.header",
    "po/insert-header.sin",
    "*/po/insert-header.sin",
    "po/insert-header.sed",
    "*/po/insert-header.sed",
    "po/quot.sed",
    "*/po/quot.sed",
    "po/remove-potcdate.sin",
    "*/po/remove-potcdate.sin",
    "po/remove-potcdate.sed",
    "*/po/remove-potcdate.sed",
]


def is_excluded(rel, patterns):
    rel = rel.as_posix()
    return any(fnmatch.fnmatch(rel, pattern) for pattern in patterns)


def find_archive(source_root, source):
    candidates = sorted((source_root / "ports").glob(source + ".tar*"))
    if not candidates:
        raise SystemExit(f"Could not find fetched archive for {source!r} under {source_root / 'ports'}")
    if len(candidates) > 1:
        names = ", ".join(str(p) for p in candidates)
        raise SystemExit(f"Multiple archives match {source!r}: {names}")
    return candidates[0]


def extract_archive(archive, tmpdir):
    with tarfile.open(archive) as tf:
        try:
            tf.extractall(tmpdir, filter="data")
        except TypeError:
            tf.extractall(tmpdir)

    entries = [p for p in tmpdir.iterdir() if p.name not in (".", "..")]
    dirs = [p for p in entries if p.is_dir()]
    if len(dirs) == 1 and len(entries) == 1:
        return dirs[0]

    # Some tarballs may not contain a single top-level directory. In that case,
    # compare against the extraction root itself.
    return tmpdir


def collect_files(root, excludes):
    files = set()
    for dirpath, dirnames, filenames in os.walk(root):
        dirpath = Path(dirpath)
        rel_dir = dirpath.relative_to(root)
        dirnames[:] = [
            d for d in dirnames
            if not is_excluded(rel_dir / d, excludes)
        ]
        for name in filenames:
            rel = rel_dir / name
            if not is_excluded(rel, excludes):
                files.add(rel)
    return files


def read_text(path):
    data = path.read_bytes()
    if b"\0" in data:
        return None
    return data.decode("utf-8", errors="surrogateescape").splitlines(keepends=True)


def make_diff(original, current, excludes):
    rels = sorted(collect_files(original, excludes) | collect_files(current, excludes))
    chunks = []

    for rel in rels:
        old_path = original / rel
        new_path = current / rel
        old_lines = [] if not old_path.exists() else read_text(old_path)
        new_lines = [] if not new_path.exists() else read_text(new_path)

        if old_lines is None or new_lines is None:
            if old_path.exists() != new_path.exists() or old_path.read_bytes() != new_path.read_bytes():
                chunks.append(f"Binary files a/{rel.as_posix()} and b/{rel.as_posix()} differ\n")
            continue

        if old_lines == new_lines:
            continue

        chunks.extend(difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile=f"a/{rel.as_posix()}",
            tofile=f"b/{rel.as_posix()}",
        ))

    return "".join(chunks)


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Generate an xbstrap patch for a fetched non-git tarball source. "
            "By default, common autotools/gettext/libtool generated files are "
            "filtered out so patches stay focused after regenerate."
        )
    )
    parser.add_argument("source", help="xbstrap source name, e.g. gdbm")
    parser.add_argument(
        "-S", "--source-root",
        type=Path,
        default=Path.cwd(),
        help="bootstrap source root (default: current directory)",
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        help="write the patch to this file instead of stdout",
    )
    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        help="additional fnmatch pattern to exclude, relative to the source root",
    )
    parser.add_argument(
        "--include-generated",
        action="store_true",
        help="include generated build-system files such as configure, Makefile.in, config.sub, and libtool/gettext/autopoint files",
    )
    args = parser.parse_args()

    source_root = args.source_root.resolve()
    current = source_root / "ports" / args.source
    if not current.is_dir():
        raise SystemExit(f"Could not find checked-out source directory: {current}")

    archive = find_archive(source_root, args.source)
    excludes = ALWAYS_EXCLUDES + list(args.exclude)
    if not args.include_generated:
        excludes = GENERATED_BUILD_SYSTEM_EXCLUDES + excludes

    with tempfile.TemporaryDirectory(prefix=f"{args.source}-patch-") as tmp:
        original = extract_archive(archive, Path(tmp))
        patch = make_diff(original, current, excludes)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(patch)
    else:
        sys.stdout.write(patch)

    if not patch:
        print(f"No differences for {args.source}", file=sys.stderr)


if __name__ == "__main__":
    main()
