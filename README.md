# SVreborn project

(Haven't yet decided on the best name, none really sound super good, lol)

This is a project about taking the original source code from the UNIX AT&T UNIX System V Release 4, and basically continuing with it, for lack of a better way to phrase it.

This includes using modern tooling to compile it, and a modern userspace.

## Current state

### What works
Userspace mostly works. X11 works, and so do most basic utilites. Mesa works, including with SSE (if you install the `mesa-sse` variant of the package), but is slow due to me not having ported LLVM and it having to use softpipe rather than LLVMpipe.

I did implement a Cirrus VGA driver; it does work, but the code is a bit clanker given how often I let that try to semi-automatically debug various issues I had, especially with 86Box (since that seems to emulate it a lot more accurately than Qemu does). The input driver is similar, but a bit less so.

### What doesn't work
Loopback networking is really messy but does kinda work. We use the original STREAMS network stack, and I haven't had too much experience with all that, and it really does confuse me quite a bit. Genuinely, no real idea how I got it to work, there was some clanker involved and several 3am nights :^)

PS/2 keyboard works in Xorg in 86box, while PS/2 mouse doesn't. Probably 86Box being more accurate in emulation than Qemu, still have to look into that.

## AI usage disclaimer

AI was used to debug a *lot* of stuff, partially due to skill issues, partially due to motivation issues, and partially due to general wanting to get things working while I looked at other stuff.
AI was also used to originally create the kernel build system, and was used to help me port it to Meson. Personally, as much as I'm not the greatest fan of AI, I think this was honestly worth it.
