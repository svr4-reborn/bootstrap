This is the bootstrap folder for a UNIX System V kernel based distribution. The build system is based on xbstrap, with the build folder itself being located in `../svr4-bootstrap-build`.
Packages are generally cloned into the `ports/` folder, with the exception of the C library (mlibc), which is under `mlibc/`, and the kernel iself (package name `uts`), which is under `uts/`. These folders are excluded from the repo via `.gitignore`; if you wish to search in them, manually use `rg` inside the folders themselves, but only do this sparingly inside `ports/` due to the sheer amount of possible files in there (using ripgrep inside `mlibc/` is absolutely OK though).

# mlibc

We use the mlibc C library. It is a highly portable and quite compatiable C client. Our sysdeps (so the parts that add support for our OS) are under `mlibc/sysdeps/svr4`. If there are ABI header issues in packages (such as missing defines), it is likely that either something is missing there, or that we just plainly don't have a equivalent define/header/feature for it. Search the kernel for more information.

# The kernel

This project is about porting a modern userland to the original AT&T UNIX System V Release 4 kernel. Therefore, the kernel itself is derived directly from that original source code, although several changes and improvements have been made already.

## How to handle missing features, functionality or drivers

***Always ask first***, but in general, as a simple approximate guide *for the kernel itself (not mlibc)*:
- Bugs are always to be fixed.
- Simple things that can be implemented as pure additions (eg. without affecting syscall behaviour, and generally leaving things in place so that older, original classic software can, at least in theory, still run) are generally OK, and preferred to hacky workarounds, missing features, etc.
- More complex refactors that can still be implemented as pure additions but require more effort, time, code, etc, can still be prefered to missing features or general hackyness/workarounds, but need more considering.
- In general, try to abstain from changing the functionality of existing syscalls/ABI, in ways that would break old code.

For changes to mlibc:
- Keep things to the sysdeps if at all possible.
- If something in mlibc outside of there needs to be changed, consider recommending that the relevant parts be moved to the sysdeps if possible, either as a bit header or as a sysdep function (see the code for more details, if relevant).

## Some more potentially helpful details

The kernel is, obviously, based on a literal UNIX, so quite often, things do just end up working. However, bearing the restrictions above in mind, when they don't, we aim to match *POSIX*.

It is for the most part quite ancient code, so a lot of it is in K&R style C. If you make changes, follow these guidelines:
- If you are making small adjustments to a function, keep the style of the file in general intact.
- If you are making a new file, format it as modern ANSI C.
- If you are making substantial changes/rewrites to a function, rewrite that function to ANSI C.
- If you are making substantial changes/rewrites to a file as a whole, rewrite that file to ANSI C.
- Before making edits to a file, briefly take a look over it to verify what style that file is in.
The end goal, over time, would be to slowly reformat the kernel source code to ANSI C, while modernizing it.

It is 32-bit, and compiled with the i686. It does not support SSE or any instructions that need XSAVE.

# xbstrap itself

Common xbstrap commands include (in step order, in most cases, commands will include the previous steps if not already done):
- xbstrap fetch {source_name} -> fetches the source file itself
- xbstrap checkout {source_name} -> checks the source out (in case of tar files, extracts them, in case of git repos, runs the needed commands)
- xbstrap patch {source_name} -> applies any patch files (if present) from the relevant source
- xbstrap regenerate {source_name} -> runs the regenerate steps of the source, if present
- xbstrap configure {package_name} -> runs the configure section of the recipe for the package
- xbstrap build {package_name} -> builds the package itself
  - Can take `--reconfigure` as an argument to also reconfigure the package
- xbstrap install {package_name} -> installs the built package
  - Can take `--reconfigure` as an argument to also reconfigure the package, or `--rebuild` to just rebuild it

Tools are built with their own set of arguments; view them with `xbstrap --help` if that or something more complex is relevant.

You can run these commands with `-n` as a dry-run; the dependency solver will then print a list of what steps it would do (including building dependencies, if not built, and including creating the temporary build sysroot with the dependencies the package requires).

Many users have aliases for these commands. These can differ and may not be available in your enviroment; if relevant, try to view local aliases set, but some of the common ones take these forms:
- xbi -> xbstrap install
- xbic -> xbstrap install --reconfigure
- xbib -> xbstrap install --rebuild
- xbit -> xbstrap install-tool 

`bootstrap.yml` contains basic info about the bootstrap system; sources, tools and packages are defined under relevant files in `bootstrap.d`; organised under categories that match which categories a package would fall under in Gentoo.

## How to handle adding patches

Generally speaking, due to it being easier to produce patches for, using git repositories for new packages is encouraged. This makes adding new patches easier as well: if you make a change to a package to fix something, you can commit it ***inside the package port folder itself (verify your command is right first!)*** and use `git format-patch -{amount of commits} HEAD` to create suitable patch files, which you can them move to the appropriate folder under `patches/` (make one if it doesn't exist)

For non-git repositories, generally speaking, just note you made changes and tell the user to create/update patches if needed; making patches for that takes quite a bit of time and tokens, both of which are costly.

## How to handle old-SYSV-assuming stuff

In build scripts:
- Our toolchain is fully modern
- Therefore -> make it assume modern stuff

Avoid removing the old cases if possible; either gate on the versions of the relevant tools, if that isn't too complex, or gate on our mlibc C library. Only remove it fully if nothing else is easy to do, wasting time splitting hairs on that isn't great either.

In code:
- The kernel itself is still quite old, so often it can still be correct logic
- However: our userspace is modern, so if relevant, add a "not-mlibc" define check to it (our GCC defines `__mlibc__` as a define, so we can safely use that)

