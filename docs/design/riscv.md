# RISC-V on the Tang Nano 20K, and what "XNU / Darwin" would take

Budget: 20 736 LUT4, 828 Kbit BSRAM, 8 MB SDR SDRAM, 8 MB SPI flash, 1.0 s-class reload for multiboot.
Everything below is a desk study. **Nothing in this list has been built or run on this board by MiSTang yet** (status column).

## Soft cores worth a slot (as MiSTang "cores")

| Core | ISA | Rough size | MMU | Why / limit | Status |
|---|---|---|---|---|---|
| FemtoRV32 Quark/RV32E | RV32E | ~550 LUT (measured in Open Pocket GBC) | no | already the menu CPU in the launcher | **running** (menu firmware) |
| SERV | RV32I bit-serial | a few hundred LUT | no | smallest; good for tests and tiny shells | not tried |
| PicoRV32 | RV32IMC | ~1–2k LUT | no | simple, well documented, many SoC examples | not tried |
| NEORV32 | RV32IMC(+Zicsr…) | ~2–4k LUT | no | complete SoC, UART/SPI/GPIO, Gowin-friendly VHDL | not tried |
| VexRiscv (LiteX) | RV32IMA(+MMU) | 2–6k LUT by config | optional | the common choice for LiteX; the MMU variant is what Linux needs | not tried |
| Hazard3 / Ibex | RV32IMC | 3–6k LUT | no | larger, better CPI | not tried |

Run-from: the core's firmware lives in the same flash slot as its bitstream, or on the SD card through the launcher loader.

## What can run on top

| Software | Needs | Realistic here |
|---|---|---|
| Bare-metal C, Zephyr, FreeRTOS | nothing | yes, on any core above |
| BASIC / Forth / small monitors | nothing | yes |
| uClinux (Linux **nommu**) + busybox | RV32 with M/A, ≥ 4–8 MB RAM, UART | plausible on VexRiscv/PicoRV32; the 8 MB SDRAM is the limit, expect tight |
| Linux with MMU | VexRiscv MMU variant, 16–32 MB RAM typical | **not with 8 MB**; LiteX boards that do it carry 32 MB or more |
| zsh | libc, fork/exec, a TTY | needs a Linux userland with MMU; bash/ash under busybox is the realistic shell |
| fastfetch / neofetch | libc, `/proc` and `/sys`, an OS; neofetch is a bash script | only after a Linux boots; neofetch needs bash + coreutils, fastfetch is C but pulls many libs |

## XNU / Darwin

Not feasible on this board, and not just because of size:

- **No RISC-V port exists.** Apple's open-source XNU builds for x86_64 and arm64 only. A port means a new `osfmk/riscv` machine layer (pmap, exceptions, context switch, interrupts), a bootloader and a device tree, and a toolchain that targets Darwin on RISC-V.
- **64-bit assumption.** XNU is a 64-bit kernel; the soft cores that fit here are RV32.
- **Memory.** Even a stripped-down XNU plus launchd wants hundreds of megabytes. The board has 8 MB of RAM.
- **Userland.** zsh and fastfetch on "Darwin" would need the Darwin libc/dyld/launchd stack, which is again arm64/x86_64 only. On RISC-V the usable stack is Linux (or a BSD such as FreeBSD/NetBSD, which do support RISC-V) with musl or glibc.

What is possible instead, in order of effort:
1. Run a RISC-V soft core with a monitor or bare-metal programs (days).
2. uClinux nommu + busybox shell, with a static `neofetch`-like script in `ash` (weeks, memory-bound).
3. For real Darwin/zsh/fastfetch, use a bigger FPGA board (64-bit RV with MMU and ≥ 256 MB DDR, e.g. Linux-capable boards) or QEMU `virt` for RISC-V; XNU itself would still be a research port.

Because of the porting policy (see README), a RISC-V core would be a MiSTang core repo from the template, built from the upstream project's HDL with its license kept.
