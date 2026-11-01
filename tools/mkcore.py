#!/usr/bin/env python3
"""Package a Gowin bitstream (.fs or .bin) as a MiSTang core: patch the multiboot header so
RECONFIG_N returns to the launcher, write <id>.bin + <id>.json.
usage: mkcore.py core.fs --id nes --name "NES" --ext nes,fds [--multiboot 0x0] [-o outdir]"""
import argparse, json, pathlib, struct, sys, hashlib
KEYLEN = {0x06: 8, 0x0A: 4, 0x0B: 4, 0x10: 8, 0x12: 4, 0x51: 8, 0x52: 8, 0x3B: 4}

def load(path):
    raw = pathlib.Path(path).read_bytes()
    if raw[:1] in (b'/', b'0', b'1'):  # ASCII .fs
        out = bytearray()
        for line in raw.decode().splitlines():
            if not line or line[0] == '/': continue
            out += int(line, 2).to_bytes(len(line) // 8, 'big')
        raw = bytes(out)
    return bytearray(raw)

def header(b):
    p = 0
    while b[p] == 0xFF: p += 1
    if b[p:p+2] != b'\xa5\xc3': sys.exit('not a Gowin bitstream')
    p += 2; h = {}
    while True:
        k = b[p] & 0x7F; n = KEYLEN.get(k) or sys.exit(f'unknown header key {k:#x}')
        if k == 0x06: h['idcode'] = struct.unpack('>I', b[p+4:p+8])[0]
        if k == 0x52: h['mb_off'] = p + 4; h['multiboot'] = struct.unpack('>I', b[p+4:p+8])[0]
        p += n
        if k == 0x3B: return h

ap = argparse.ArgumentParser(); ap.add_argument('src'); ap.add_argument('--id', required=True); ap.add_argument('--name')
ap.add_argument('--ext', default=''); ap.add_argument('--multiboot', default='0x0'); ap.add_argument('-o', default='.')
a = ap.parse_args()
b = load(a.src); h = header(b)
if h.get('idcode') != 0x0000081B: sys.exit(f"IDCODE {h.get('idcode', 0):#x} is not GW2A(R)-18")
if 'mb_off' not in h: sys.exit('no multiboot header line')
mb = int(a.multiboot, 16)
if mb % 4096: sys.exit('multiboot address must be 4 KiB aligned')
b[h['mb_off']:h['mb_off']+4] = struct.pack('>I', mb)
out = pathlib.Path(a.o); out.mkdir(parents=True, exist_ok=True)
(out / f'{a.id}.bin').write_bytes(b)
(out / f'{a.id}.json').write_text(json.dumps(dict(id=a.id, name=a.name or a.id, ext=[e for e in a.ext.split(',') if e],
    size=len(b), multiboot=mb, sha256=hashlib.sha256(b).hexdigest()), indent=1))
print(f'{a.id}: {len(b)} bytes, multiboot {h["multiboot"]:#x} -> {mb:#x}')
