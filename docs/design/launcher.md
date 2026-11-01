# MiSTang launcher design

Goal: one Tang Nano 20K, many cores, chosen from an SD-card menu, no host PC needed after setup.

## Flash map (8 MiB, W25Q64 — verified)
| Offset | Content |
|---|---|
| 0x000000 | Launcher bitstream, header multiboot → 0x400000 |
| 0x100000 | Launcher firmware (u32 length + RV32E code; same loader as Open Pocket GBC) |
| 0x200000 | Registry / settings / per-core config |
| 0x400000 | **Core slot A** (≤ 1 MiB), header multiboot → 0x000000 |
| 0x500000 | Core slot B (pinned core, optional) |
| 0x7FF000 | System settings |

Caveat found while testing: a board that previously ran Open Pocket GBC has ROMs, saves and settings over most of this range. Studio's raw-write refuses nothing — back up first (`openFPGALoader --dump-flash`).

## Boot-a-core sequence
1. Menu CPU reads `/MiSTang/cores/<id>.json` + `.bin` from SD (FatFs).
2. Compare `sha256` with the copy in slot A (stored in the registry); skip copy if equal.
3. Erase 4 KiB sectors, program 256 B pages, verify.
4. Drive `RECONFIG_N` low ≥ 1 µs. The FPGA reconfigures from the multiboot address in the **currently loaded** bitstream header — that is why the launcher is built with `--multiboot_address 0x400000`.
5. A core pulls `RECONFIG_N` on (SELECT+START held 1 s) → loads 0x000000 = launcher.

Gowin parameters (UG290/UG702): address granularity 4 KiB; do **not** build with `--reconfign_as_gpio`; rate in the header is fixed by Apicula.

## Open items (not yet verified on hardware)
- ~~RECONFIG_N reachable from fabric~~ **verified 2026-11-01**: pin 9 (IOR31B) driven low from fabric reloads the FPGA from the multiboot address in the loaded bitstream header (`hwtest/reconfig`). Constraint: `IO_LOC "recon" 9;` as `inout`, driven `1'b0 : 1'bz`; do not pass `--reconfign_as_gpio`.
- Still to test: return trip from a core booted out of flash, and switching time (an Apicula user measured ~1.7 s on another Tang board).
- Per-core shared services: HDMI scaler, SPI LCD, audio, SD/ROM loader live in the launcher; cores get them as a small wrapper (`mistang_core_if.sv`, planned) so porting a MiSTer core is mostly glue around `hps_io`.

## Core package (`/MiSTang/cores/<id>.json`)
```json
{"id":"nes","name":"NES","ext":["nes","fds"],"size":907418,"multiboot":0,"sha256":"…"}
```
Create with `tools/mkcore.py` or Studio → SD card.
