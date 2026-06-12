# Jinx to xbstrap migration audit

Generated from the old Jinx tree under `uts/` and the current xbstrap recipes under `bootstrap.d/`.

Patch status means:

- `old`: a patch directory exists only under `uts/patches/<name>`.
- `new`: a patch directory exists only under `patches/<name>`.
- `old+new`: both trees have a patch directory; compare before dropping either side.

## Source recipes

7/14 already have a matching xbstrap entry.

| Done | Name | Status | Version | Revision | Patches | Dependencies | Custom steps | Old recipe |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [ ] | `autoconf` | missing | 2.72 | - | old | - | - | `uts/source-recipes/autoconf` |
| [ ] | `automake` | missing | 1.16.5 | - | - | - | - | `uts/source-recipes/automake` |
| [ ] | `binutils` | present | 2.44 | 1 | old+new | libtool pkg-config build-essential | prepare | `uts/source-recipes/binutils` |
| [ ] | `cmake` | missing | 4.0.0 | - | - | - | - | `uts/source-recipes/cmake` |
| [ ] | `gcc` | present | 15.1.0 | - | old+new | libtool pkg-config git build-essential | prepare | `uts/source-recipes/gcc` |
| [x] | `gettext` | present | 0.23.1 | 1 | - | automake autoconf libtool pkg-config | prepare | `uts/source-recipes/gettext` |
| [ ] | `libgcc-binaries` | missing | 6097e89af23cc4eec9f31a5a089f93c35e63edef | - | - | - | - | `uts/source-recipes/libgcc-binaries` |
| [x] | `libtool` | present | 2.5.4 | - | - | autoconf automake | prepare | `uts/source-recipes/libtool` |
| [x] | `mlibc` | present | 6.3.0 | - | - | - | - | `uts/source-recipes/mlibc` |
| [x] | `pkg-config` | present | 2.3.0 | - | - | autoconf automake libtool | prepare | `uts/source-recipes/pkg-config` |
| [x] | `uts` | present | 0.1 | - | - | - | - | `uts/source-recipes/uts` |
| [ ] | `xorg-font-util` | missing | 1.20.2 | 1 | - | autoconf automake libtool xorg-macros | prepare | `uts/source-recipes/xorg-font-util` |
| [ ] | `xorg-util-macros` | missing | 1.20.2 | 1 | - | autoconf automake libtool | prepare | `uts/source-recipes/xorg-util-macros` |
| [ ] | `xtrans` | missing | 1.6.0 | 1 | - | autoconf automake libtool xorg-macros pkg-config | prepare | `uts/source-recipes/xtrans` |

## Host-Tool recipes

2/11 already have a matching xbstrap entry.

| Done | Name | Status | Version | Revision | Patches | Dependencies | Custom steps | Old recipe |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [ ] | `autoconf` | missing | - | 1 | old | - | configure, build, package | `uts/host-recipes/autoconf` |
| [ ] | `automake` | missing | - | 1 | - | autoconf build-essential | configure, build, package | `uts/host-recipes/automake` |
| [ ] | `binutils` | missing | - | 1 | old+new | libtool pkg-config build-essential | configure, build, package | `uts/host-recipes/binutils` |
| [ ] | `cmake` | missing | - | 1 | - | build-essential cmake libssl-dev | configure, build, package | `uts/host-recipes/cmake` |
| [ ] | `gcc` | missing | - | 1 | old+new | libtool pkg-config binutils mlibc-headers build-essential | configure, build, package | `uts/host-recipes/gcc` |
| [ ] | `libgcc-binaries` | missing | - | 1 | - | - | package | `uts/host-recipes/libgcc-binaries` |
| [x] | `libtool` | present | - | 1 | - | autoconf automake help2man build-essential | configure, build, package | `uts/host-recipes/libtool` |
| [x] | `pkg-config` | present | - | 1 | - | automake autoconf libtool build-essential | configure, build, package | `uts/host-recipes/pkg-config` |
| [ ] | `xorg-font-util` | missing | - | 1 | - | build-essential pkg-config | configure, build, package | `uts/host-recipes/xorg-font-util` |
| [ ] | `xorg-macros` | missing | - | 1 | - | - | configure, build, package | `uts/host-recipes/xorg-macros` |
| [ ] | `xtrans` | missing | - | 1 | - | build-essential pkg-config | configure, build, package | `uts/host-recipes/xtrans` |

## Package recipes

11/94 already have a matching xbstrap entry.

| Done | Name | Status | Version | Revision | Patches | Dependencies | Custom steps | Old recipe |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [ ] | `base-files` | missing | 0.0 | 4 | - | - | package | `uts/recipes/base-files` |
| [ ] | `bash` | missing | 5.3.p${_patch} | 1 | - | gcc pkg-config core-libs ncurses readline build-essential | prepare, configure, build, package | `uts/recipes/bash` |
| [ ] | `brotli` | missing | 1.2.0 | 1 | - | gcc pkg-config core-libs | configure, build, package | `uts/recipes/brotli` |
| [ ] | `bzip2` | missing | 1.0.8 | 1 | - | gcc pkg-config core-libs | build, package | `uts/recipes/bzip2` |
| [ ] | `core-libs` | missing | 0.0 | 1 | - | mlibc libgcc libstdc++ libintl libiconv tzdata libxcrypt libatomic | - | `uts/recipes/core-libs` |
| [ ] | `coreutils` | missing | 9.7 | 1 | old | gcc pkg-config core-libs | prepare, configure, build, package | `uts/recipes/coreutils` |
| [ ] | `fontconfig` | missing | 2.17.1 | 2 | - | gcc pkg-config core-libs freetype2 libexpat libxml2 gperf | configure, build, package | `uts/recipes/fontconfig` |
| [x] | `freestnd-c-hdrs` | present | 87956bbcad0e1934e708223913be53131311342d | 1 | - | - | build, package | `uts/recipes/freestnd-c-hdrs` |
| [x] | `freestnd-cxx-hdrs` | present | 1cc6d4665e1e0ce4408c94616c8c4de4c19b9968 | 1 | - | - | build, package | `uts/recipes/freestnd-cxx-hdrs` |
| [ ] | `freetype2` | missing | 2.14.3 | 1 | - | gcc pkg-config core-libs bzip2 libpng brotli zlib | configure, build, package | `uts/recipes/freetype2` |
| [x] | `frigg` | present | b0dbea66bc19f7c5546f0039a3be842feb02678c | 1 | - | pkg-config meson ninja-build | configure, build, package | `uts/recipes/frigg` |
| [ ] | `gdbm` | missing | 1.25 | 1 | old | gcc pkg-config core-libs readline | prepare, configure, build, package | `uts/recipes/gdbm` |
| [ ] | `glu` | missing | 9.0.3 | 1 | - | gcc pkg-config core-libs mesa | configure, build, package | `uts/recipes/glu` |
| [ ] | `icu` | missing | 78.3 | 3 | old | gcc pkg-config core-libs | prepare, configure, build, package | `uts/recipes/icu` |
| [ ] | `libX11` | missing | 1.8.13 | 1 | - | gcc pkg-config xtrans automake autoconf libtool xorg-macros pkg-config xtrans core-libs xorg-proto libXau libXdmcp libxtrans libxcb build-essential | prepare, configure, build, package | `uts/recipes/libX11` |
| [ ] | `libXau` | missing | 1.0.12 | 1 | - | gcc pkg-config automake autoconf libtool xorg-macros pkg-config xorg-proto meson ninja-build | configure, build, package | `uts/recipes/libXau` |
| [ ] | `libXaw` | missing | 1.0.16 | 1 | - | gcc pkg-config core-libs libXmu libXpm | prepare, configure, build, package | `uts/recipes/libXaw` |
| [ ] | `libXdmcp` | missing | 1.1.5 | 1 | - | gcc pkg-config automake autoconf libtool xorg-macros pkg-config xorg-proto | prepare, configure, build, package | `uts/recipes/libXdmcp` |
| [ ] | `libXext` | missing | 1.3.7 | 1 | - | gcc pkg-config xtrans automake autoconf libtool xorg-macros pkg-config xtrans core-libs xorg-proto libX11 libxtrans xorg-util-macros build-essential | prepare, configure, build, package | `uts/recipes/libXext` |
| [ ] | `libXfixes` | missing | 6.0.2 | 1 | - | gcc pkg-config core-libs xorg-proto libX11 | configure, build, package | `uts/recipes/libXfixes` |
| [ ] | `libXfont2` | missing | 2.0.7 | 1 | - | gcc pkg-config xtrans automake autoconf libtool xorg-macros pkg-config xtrans core-libs xorg-proto libfontenc libxtrans bzip2 zlib xorg-util-macros build-essential | prepare, configure, build, package | `uts/recipes/libXfont2` |
| [ ] | `libXft` | missing | 2.3.9 | 2 | - | gcc pkg-config core-libs xorg-util-macros xorg-proto libX11 libXrender freetype2 fontconfig | configure, build, package | `uts/recipes/libXft` |
| [ ] | `libXi` | missing | 1.8.2 | 1 | - | gcc pkg-config core-libs xorg-proto libXext libXfixes | prepare, configure, build, package | `uts/recipes/libXi` |
| [ ] | `libXmu` | missing | 1.3.1 | 1 | - | gcc pkg-config xtrans automake autoconf libtool xorg-macros pkg-config xtrans core-libs xorg-proto libX11 libXext libXt libxtrans xorg-util-macros build-essential | prepare, configure, build, package | `uts/recipes/libXmu` |
| [ ] | `libXpm` | missing | 3.5.19 | 1 | - | gcc pkg-config core-libs libXext libXt | prepare, configure, build, package | `uts/recipes/libXpm` |
| [ ] | `libXrandr` | missing | 1.5.5 | 1 | - | gcc pkg-config core-libs xorg-proto libX11 libXrender libXext | prepare, configure, build, package | `uts/recipes/libXrandr` |
| [ ] | `libXrender` | missing | 0.9.12 | 1 | - | gcc pkg-config core-libs xorg-proto libX11 | prepare, configure, build, package | `uts/recipes/libXrender` |
| [ ] | `libXshmfence` | missing | 1.3.3 | 1 | - | gcc pkg-config core-libs xorg-proto | prepare, configure, build, package | `uts/recipes/libXshmfence` |
| [ ] | `libXt` | missing | 1.3.7 | 1 | - | gcc pkg-config xtrans automake autoconf libtool xorg-macros pkg-config xtrans core-libs xorg-proto libice libsm libX11 libxtrans xorg-util-macros build-essential | prepare, configure, build, package | `uts/recipes/libXt` |
| [ ] | `libXxf86vm` | missing | 1.1.7 | 1 | - | gcc pkg-config core-libs xorg-proto libXext | configure, build, package | `uts/recipes/libXxf86vm` |
| [x] | `libatomic` | present | - | 1 | - | gcc pkg-config mlibc libgcc libstdc++ build-essential | build, package | `uts/recipes/libatomic` |
| [ ] | `libbsd` | missing | 0.12.2 | 1 | old | gcc pkg-config automake autoconf libtool core-libs | prepare, configure, build, package | `uts/recipes/libbsd` |
| [ ] | `libexpat` | missing | 2.7.3 | 1 | old | gcc pkg-config cmake core-libs | configure, build, package | `uts/recipes/libexpat` |
| [ ] | `libffi` | missing | 3.4.6 | 1 | - | gcc autoconf automake libtool pkg-config core-libs | prepare, configure, build, package | `uts/recipes/libffi` |
| [ ] | `libfontenc` | missing | 1.1.9 | 1 | - | gcc pkg-config xtrans xorg-font-util automake autoconf libtool xorg-macros pkg-config xtrans xorg-font-util core-libs xorg-util-macros xorg-proto libX11 libxtrans xorg-font-util zlib build-essential | prepare, configure, build, package | `uts/recipes/libfontenc` |
| [x] | `libgcc` | present | - | 1 | - | gcc libtool pkg-config mlibc libgcc-static build-essential | build, package | `uts/recipes/libgcc` |
| [ ] | `libgcc-static` | missing | - | 1 | - | gcc libtool pkg-config build-essential | build, package | `uts/recipes/libgcc-static` |
| [ ] | `libice` | missing | 1.1.2 | 1 | - | gcc pkg-config xtrans automake autoconf libtool xorg-macros pkg-config xtrans core-libs xorg-util-macros xorg-proto libX11 libxtrans build-essential | prepare, configure, build, package | `uts/recipes/libice` |
| [ ] | `libiconv` | missing | 1.18 | 1 | - | gcc autoconf automake libtool pkg-config mlibc libgcc libstdc++ binutils | prepare, configure, build, package | `uts/recipes/libiconv` |
| [ ] | `libintl` | missing | - | 1 | - | gcc automake autoconf libtool pkg-config mlibc libgcc libstdc++ libiconv | configure, build, package | `uts/recipes/libintl` |
| [ ] | `libpng` | missing | 1.6.58 | 1 | - | gcc pkg-config cmake core-libs zlib | configure, build, package | `uts/recipes/libpng` |
| [ ] | `libsm` | missing | 1.1.2 | 1 | - | gcc pkg-config xtrans automake autoconf libtool xorg-macros pkg-config xtrans core-libs xorg-util-macros xorg-proto libice libX11 libxtrans build-essential | prepare, configure, build, package | `uts/recipes/libsm` |
| [x] | `libsmarter` | present | 338cce63b22c85557c9274ad8ecfc8423a14024d | 1 | - | gcc pkg-config meson ninja-build | configure, build, package | `uts/recipes/libsmarter` |
| [x] | `libstdc++` | present | - | 1 | - | gcc libtool pkg-config mlibc libgcc build-essential | build, package | `uts/recipes/libstdc++` |
| [ ] | `libxcb` | missing | 1.17.0 | 1 | old | gcc pkg-config automake autoconf libtool xorg-macros pkg-config xorg-proto libXau libXdmcp xcb-proto xorg-util-macros | prepare, configure, build, package | `uts/recipes/libxcb` |
| [ ] | `libxcrypt` | missing | 4.4.38 | 1 | - | gcc pkg-config mlibc libgcc libstdc++ libatomic python3-passlib | prepare, configure, build, package | `uts/recipes/libxcrypt` |
| [ ] | `libxcvt` | missing | 0.1.3 | 1 | - | gcc pkg-config core-libs meson ninja-build | configure, build, package | `uts/recipes/libxcvt` |
| [ ] | `libxkbfile` | missing | 1.2.0 | 1 | - | gcc pkg-config xtrans automake autoconf libtool xorg-macros pkg-config xtrans core-libs xorg-proto libX11 libxtrans xorg-util-macros meson ninja-build | configure, build, package | `uts/recipes/libxkbfile` |
| [ ] | `libxml2` | missing | 2.15.3 | 1 | - | gcc pkg-config core-libs icu readline zlib | configure, build, package | `uts/recipes/libxml2` |
| [ ] | `libxshmfence` | missing | 1.3.3 | 1 | - | gcc pkg-config automake autoconf libtool xorg-macros pkg-config core-libs xorg-util-macros xorg-proto libX11 libxtrans build-essential | prepare, configure, build, package | `uts/recipes/libxshmfence` |
| [ ] | `libxtrans` | missing | - | 1 | - | gcc pkg-config xtrans automake autoconf libtool xorg-macros pkg-config xtrans xorg-proto libxcb build-essential | configure, build, package | `uts/recipes/libxtrans` |
| [ ] | `lz4` | missing | 1.10.0 | 1 | - | gcc pkg-config core-libs | configure, build, package | `uts/recipes/lz4` |
| [ ] | `mesa` | missing | 26.1.2 | 1 | old | gcc pkg-config core-libs libexpat libX11 libxcb libXext libXshmfence libXxf86vm libXrandr zlib zstd python3-mako python3-yaml glslang-tools | configure, build, package | `uts/recipes/mesa` |
| [ ] | `mesa-demos` | missing | 9.0.0 | 3 | old | gcc pkg-config core-libs freetype2 mesa glu libX11 libXext | configure, build, package | `uts/recipes/mesa-demos` |
| [x] | `mlibc` | present | - | 6 | - | gcc pkg-config libgcc-binaries mlibc-headers build-essential meson ninja-build | configure, build, package | `uts/recipes/mlibc` |
| [x] | `mlibc-headers` | present | - | 1 | - | pkg-config meson ninja-build | configure, build, package | `uts/recipes/mlibc-headers` |
| [ ] | `ncurses` | missing | 6.5.${_snapshot} | 1 | old | gcc pkg-config core-libs build-essential ncurses-bin patchelf | prepare, configure, build, package | `uts/recipes/ncurses` |
| [ ] | `openssl` | missing | 3.6.1 | 1 | old | gcc pkg-config core-libs zlib | configure, build, package | `uts/recipes/openssl` |
| [ ] | `pixman` | missing | 0.46.4 | 1 | - | gcc pkg-config core-libs meson ninja-build | configure, build, package | `uts/recipes/pixman` |
| [ ] | `python` | missing | 3.13.3 | 1 | old | gcc pkg-config core-libs bzip2 xz zlib openssl ncurses readline gdbm libexpat libffi | prepare, configure, build, package | `uts/recipes/python` |
| [ ] | `readline` | missing | 8.3p${_patch} | 1 | old | gcc pkg-config core-libs ncurses | prepare, configure, build, package | `uts/recipes/readline` |
| [ ] | `svr4_init` | missing | 1.0 | 1 | - | gcc mlibc build-essential meson ninja-build | configure, build, package | `uts/recipes/svr4_init` |
| [ ] | `svr4_iputils` | missing | 1.0 | 1 | - | gcc mlibc build-essential meson ninja-build | configure, build, package | `uts/recipes/svr4_iputils` |
| [ ] | `svr4_threadtests` | missing | 1.0 | 1 | - | gcc mlibc build-essential meson ninja-build | configure, build, package | `uts/recipes/svr4_threadtests` |
| [ ] | `svr4_utils` | missing | 1.0 | 1 | - | gcc core-libs build-essential meson ninja-build | configure, build, package | `uts/recipes/svr4_utils` |
| [ ] | `tzdata` | missing | 2025b | 3 | - | gcc binutils mlibc libgcc libstdc++ libatomic libintl libiconv tzdata | early_prepare, prepare, build, package | `uts/recipes/tzdata` |
| [x] | `uts` | present | - | 1 | - | gcc base-files build-essential python3 python3-venv | configure, build, package | `uts/recipes/uts` |
| [ ] | `wsdemo` | missing | 1.0 | 1 | - | gcc mlibc build-essential meson ninja-build | configure, build, package | `uts/recipes/wsdemo` |
| [ ] | `wsdiag` | missing | 1.0 | 1 | - | gcc mlibc build-essential meson ninja-build | configure, build, package | `uts/recipes/wsdiag` |
| [ ] | `xauth` | missing | 1.1.5 | 1 | - | gcc autoconf automake libtool xorg-macros xtrans autoconf automake libtool xorg-macros pkg-config xtrans xorg-proto libX11 libXau libXdmcp libXext libXmu libxtrans build-essential | prepare, configure, build, package | `uts/recipes/xauth` |
| [ ] | `xbitmaps` | missing | 1.1.4 | 1 | - | gcc pkg-config core-libs meson ninja-build | - | `uts/recipes/xbitmaps` |
| [ ] | `xcb-proto` | missing | 1.17.0 | 1 | - | gcc pkg-config automake autoconf libtool xorg-macros pkg-config core-libs xorg-proto libXau libXdmcp | prepare, configure, build, package | `uts/recipes/xcb-proto` |
| [ ] | `xdemineur` | missing | 2.1.1 | 1 | old | gcc pkg-config core-libs libX11 libXpm meson ninja-build | - | `uts/recipes/xdemineur` |
| [ ] | `xf86-input-svr4xqueue` | missing | 0.1 | 7 | - | gcc pkg-config core-libs xorg-server xorg-proto build-essential meson ninja-build | configure, build, package | `uts/recipes/xf86-input-svr4xqueue` |
| [ ] | `xf86-video-dummy` | missing | 0.4.1 | 1 | - | gcc pkg-config core-libs xorg-proto xorg-server xorg-util-macros libX11 | prepare, configure, build, package | `uts/recipes/xf86-video-dummy` |
| [ ] | `xf86-video-svr4ws` | missing | 0.1 | 8 | - | gcc pkg-config core-libs xorg-server xorg-proto build-essential meson ninja-build | configure, build, package | `uts/recipes/xf86-video-svr4ws` |
| [ ] | `xinit` | missing | 1.4.4 | 1 | - | gcc autoconf automake libtool xorg-macros xtrans autoconf automake libtool xorg-macros pkg-config xtrans core-libs svr4_utils xorg-proto libX11 xauth build-essential | prepare, configure, build, package | `uts/recipes/xinit` |
| [ ] | `xkbcomp` | missing | 1.5.0 | 2 | - | gcc pkg-config core-libs xorg-util-macros xorg-proto libX11 libxkbfile xkeyboard-config meson ninja-build | - | `uts/recipes/xkbcomp` |
| [ ] | `xkeyboard-config` | missing | 2.47 | 1 | - | gcc pkg-config xtrans automake autoconf libtool xorg-macros pkg-config xtrans core-libs xorg-util-macros xorg-proto libX11 libxtrans meson ninja-build | - | `uts/recipes/xkeyboard-config` |
| [ ] | `xorg-apps` | missing | 1.0 | 1 | - | xterm xorg-xclock xorg-xeyes xorg-xcalc xdemineur | package | `uts/recipes/xorg-apps` |
| [ ] | `xorg-drivers` | missing | 21.1 | 4 | - | xf86-video-dummy xf86-video-svr4ws xf86-input-svr4xqueue | package | `uts/recipes/xorg-drivers` |
| [ ] | `xorg-font-util` | missing | - | 1 | - | gcc pkg-config automake autoconf libtool xorg-macros pkg-config xtrans core-libs build-essential | configure, build, package | `uts/recipes/xorg-font-util` |
| [ ] | `xorg-proto` | missing | 2025.1 | 1 | old | gcc pkg-config core-libs | prepare, configure, build, package | `uts/recipes/xorg-proto` |
| [ ] | `xorg-server` | missing | 21.1.23 | 1 | old | gcc pkg-config xtrans xorg-proto xauth xinit xkbcomp xkeyboard-config xbitmaps libX11 libXau libxcvt libXdmcp libXext libXfont2 libxcb pixman libxtrans libxkbfile libxshmfence libfontenc xcb-util libbsd openssl xorg-font-util build-essential meson ninja-build | configure, build, package | `uts/recipes/xorg-server` |
| [ ] | `xorg-twm` | missing | 1.0.13.1 | 1 | - | gcc pkg-config core-libs libXmu | prepare, configure, build, package | `uts/recipes/xorg-twm` |
| [ ] | `xorg-util-macros` | missing | - | 1 | - | gcc pkg-config automake autoconf libtool xorg-macros pkg-config core-libs | configure, build, package | `uts/recipes/xorg-util-macros` |
| [ ] | `xorg-xcalc` | missing | 1.1.3 | 1 | - | gcc pkg-config core-libs libX11 libXaw libXt xorg-proto | prepare, configure, build, package | `uts/recipes/xorg-xcalc` |
| [ ] | `xorg-xclock` | missing | 1.1.1 | 3 | - | gcc pkg-config core-libs libX11 libXmu libXaw libXrender libXft libxkbfile | prepare, configure, build, package | `uts/recipes/xorg-xclock` |
| [ ] | `xorg-xeyes` | missing | 1.3.1 | 1 | - | gcc pkg-config core-libs libX11 libXi libXt libXext libXmu libXrender xorg-proto | prepare, configure, build, package | `uts/recipes/xorg-xeyes` |
| [ ] | `xorg-xmessage` | missing | 1.0.7 | 1 | - | gcc pkg-config core-libs libXaw libX11 libXt | prepare, configure, build, package | `uts/recipes/xorg-xmessage` |
| [ ] | `xterm` | missing | 410 | 1 | old | gcc pkg-config core-libs ncurses libX11 libXext libXmu libXaw libXpm libXrender libXft libxkbfile | prepare, configure, build, package | `uts/recipes/xterm` |
| [ ] | `xz` | missing | 5.6.4 | 1 | - | gcc autoconf automake libtool pkg-config core-libs | prepare, configure, build, package | `uts/recipes/xz` |
| [ ] | `zlib` | present | 1.3.1 | 1 | old | gcc pkg-config core-libs patchelf | configure, build, package | `uts/recipes/zlib` |
| [ ] | `zstd` | missing | 1.5.7 | 1 | - | cmake gcc pkg-config core-libs zlib xz lz4 | configure, build, package | `uts/recipes/zstd` |

## Patch directories

- Old-only patch directories: 18
- Present in both trees: 2

Old-only patches to review:

- [ ] `autoconf`
- [ ] `coreutils`
- [ ] `gdbm`
- [ ] `icu`
- [ ] `libbsd`
- [ ] `libexpat`
- [ ] `libxcb`
- [ ] `mesa`
- [ ] `mesa-demos`
- [ ] `ncurses`
- [ ] `openssl`
- [ ] `python`
- [ ] `readline`
- [ ] `xdemineur`
- [ ] `xorg-proto`
- [ ] `xorg-server`
- [ ] `xterm`
- [ ] `zlib`

Patch directories that exist in both places and should be diffed:

- [ ] `binutils`
- [ ] `gcc`

