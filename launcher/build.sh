#!/usr/bin/env bash
# Builds the MiSTang launcher: Open Pocket GBC gateware + one reconfig pin, with the launcher firmware.
# Output: launcher/out/launcher.fs  (bitstream, multiboot -> 0x400000)
#         launcher/out/fw.bin       (firmware, flash 0x100000)
# Needs: git, python3, oss-cad-suite (TOOLS=...), xPack riscv-none-elf-gcc on PATH.
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
OPG_REPO=${OPG_REPO:-https://github.com/LakoMoor/open-pocket-gbc}
WORK=${WORK:-$HERE/work}
OUT=$HERE/out
PY=${PY:-python3}
mkdir -p "$OUT"
if [ ! -d "$WORK/opg" ]; then git clone --depth 1 "$OPG_REPO" "$WORK/opg"; fi
rm -rf "$WORK/tree"; cp -r "$WORK/opg" "$WORK/tree"
"$PY" "$HERE/rtl/apply.py" "$WORK/tree"

# firmware: the launcher replaces main.c; the GB-specific files are left out
cd "$WORK/tree/fw"
mkdir -p build
CFLAGS="-march=rv32e -mabi=ilp32e -Os -ffreestanding -fno-delete-null-pointer-checks -ffunction-sections -fdata-sections -Wall -Wno-unused-function -Isrc -Ifatfs"
riscv-none-elf-gcc $CFLAGS -nostartfiles -T src/link.ld -Wl,--gc-sections -Wl,-Map,build/fw.map \
    -o build/fw.elf src/start.S "$HERE/fw/main.c" src/osd.c src/sd.c src/flash.c src/util.c fatfs/ff.c fatfs/ffunicode.c -lc -lgcc
riscv-none-elf-objcopy -O binary build/fw.elf build/code.bin
"$PY" - <<'PYEOF'
import struct
c = open('build/code.bin', 'rb').read(); c += b'\0' * (-len(c) % 4)
open('build/fw.bin', 'wb').write(struct.pack('<I', len(c)) + c)
print('launcher firmware', len(c), 'bytes')
PYEOF
cp build/fw.bin "$OUT/fw.bin"

# gateware: do NOT pass --reconfign_as_gpio, the pin is RECONFIG_N
cd "$WORK/tree"
# VIDEO=720p builds the 720p HDMI mode (the default is 480p)
[ "${VIDEO:-}" = 720p ] && export DEFS="-DVIDEO_720P ${DEFS:-}"
PACK_EXTRA="--mspi_as_gpio --multiboot_address 0x400000" ./build.sh gbc_top   # default OUT_DIR is relative: Windows yosys cannot open /e/... paths
cp build/gbc_top/gbc_top.fs "$OUT/launcher.fs"
echo "next: write launcher.fs to 0x000000 and fw.bin to 0x100000 (Studio > Flash, or openFPGALoader)"
