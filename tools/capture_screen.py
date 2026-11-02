#!/usr/bin/env python3
"""Screenshot of an Open Pocket-compatible core running on the Tang Nano 20K, over the board's USB-UART (interface B).
Implements the screen-stream protocol of Open Pocket GBC (command 'Q', ~1 frame/s, 160x144 + menu overlay) with the
standard library only. The picture is composed like the HDMI output: 720x480, 3x game scaling, 2x menu cells.
usage: capture_screen.py [port] out.png [--frames N]"""
import os, sys, time, termios, select, zlib, struct, re

def open_port(path, baud=115200):
    fd = os.open(path, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
    a = termios.tcgetattr(fd)
    a[0] = 0; a[1] = 0; a[2] = termios.CS8 | termios.CREAD | termios.CLOCAL; a[3] = 0
    a[4] = a[5] = getattr(termios, f'B{baud}'); a[6][termios.VMIN] = 0; a[6][termios.VTIME] = 0
    termios.tcsetattr(fd, termios.TCSANOW, a); return fd

class Parser:
    """Same framing as docs/web/protocol.mjs of open-pocket-gbc."""
    def __init__(self): self.reset(); self.packets = []; self.text = ''
    def reset(self): self.state = 'text'; self.line = ''; self.payload = []; self.words = 0
    def feed(self, data):
        for b in data:
            st = self.state
            if st == 'text':
                if b == 0: self.text += self.line; self.line = ''; self.state = 'type'
                else:
                    self.line += chr(b)
                    if b == 10 or len(self.line) >= 1024: self.text += self.line; self.line = ''
            elif st == 'type':
                self.type = chr(b); self.payload = []; self.state = 'row' if self.type == 'R' else 'low'
            elif st == 'low': self.length = b; self.state = 'high'
            elif st == 'high':
                self.length |= b << 8
                if self.length > 4096: self.reset(); continue
                self.state = 'payload'
                if not self.length: self.emit()
            elif st == 'payload':
                self.payload.append(b)
                if len(self.payload) == self.length: self.emit()
            elif st == 'row':
                if b >= 144: self.reset(); continue
                self.payload = [b]; self.words = 0; self.state = 'control'
            elif st == 'control':
                self.payload.append(b); self.run = b + 1 if b < 128 else b - 126
                if self.words + self.run > 80: self.reset(); continue
                self.words += self.run; self.remaining = self.run * 4 if b < 128 else 4; self.state = 'pixels'
            elif st == 'pixels':
                self.payload.append(b); self.remaining -= 1
                if self.remaining == 0:
                    if self.words == 80: self.emit()
                    else: self.state = 'control'
    def emit(self): self.packets.append((self.type, bytes(self.payload))); self.state = 'text'; self.payload = []

def decode_row(t, p):
    if not p or p[0] >= 144 or t not in 'GR': return None
    unit = 4 if t == 'R' else 2; px = []; at = 1
    while at < len(p) and len(px) < 160:
        c = p[at]; at += 1; count = c + 1 if c < 128 else c - 126; units = count if c < 128 else 1
        if at + units * unit > len(p): return None
        for n in range(count):
            q = at + (n * unit if c < 128 else 0); px.append(p[q] | p[q + 1] << 8)
            if unit == 4: px.append(p[q + 2] | p[q + 3] << 8)
        at += units * unit
    return (p[0], px) if len(px) == 160 and at == len(p) else None

PALETTE = [0x101010,0,0x0f380f,0x242424,0x3c3c3c,0x7a7a7a,0xbebebe,0xffffff,0x3a6ff0,0x9bbc0f,0xf5c518,0xe5483c,0x306230,0x0e1a33,0x8bac0f,0]

def png(path, w, h, rgb):
    raw = b''.join(b'\0' + rgb[y * w * 3:(y + 1) * w * 3] for y in range(h))
    def ch(t, d): c = struct.pack('>I', len(d)) + t + d; return c + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    open(path, 'wb').write(b'\x89PNG\r\n\x1a\n' + ch(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0)) + ch(b'IDAT', zlib.compress(raw, 6)) + ch(b'IEND', b''))

def compose(fb, gbc, raw, dmg, flags, cells, font):
    W, H = 720, 480; img = bytearray(W * H * 3); dim = .4 if (flags & 3) == 3 else 1
    def rgb(v):
        if not gbc: return dmg[v & 3]
        r, g, b = v & 31, v >> 5 & 31, v >> 10 & 31
        if raw: return (r << 3 | r >> 2) << 16 | (g << 3 | g >> 2) << 8 | (b << 3 | b >> 2)
        return min(255, (r * 26 + g * 4 + b * 2) >> 2) << 16 | min(255, (g * 24 + b * 8) >> 2) << 8 | min(255, (r * 6 + g * 4 + b * 22) >> 2)
    def put(x, y, c, k=1):
        o = (y * W + x) * 3; img[o] = int((c >> 16) * k); img[o + 1] = int((c >> 8 & 255) * k); img[o + 2] = int((c & 255) * k)
    for y in range(144):
        for x in range(160):
            c = rgb(fb[y * 160 + x])
            for yy in range(3):
                for xx in range(3): put(120 + x * 3 + xx, 24 + y * 3 + yy, c, dim)
    if flags & 1 and cells:
        for cy in range(24):
            for cx in range(42):
                v = cells[cy * 42 + cx]; attr = v >> 8; ch = v & 127; ext = v & 128
                for py in range(10):
                    fy = py - 1; bits = (font[ch * 8 + (0 if fy < 0 else 7)] if ext else 0) if fy < 0 or fy > 7 else font[ch * 8 + fy]
                    for px in range(8):
                        ci = (attr & 15) if bits >> (7 - px) & 1 else attr >> 4
                        if not ci: continue
                        for yy in range(2):
                            for xx in range(2): put(24 + (cx * 8 + px) * 2 + xx, (cy * 10 + py) * 2 + yy, PALETTE[ci])
    return W, H, bytes(img)

def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    port = args[0] if len(args) > 1 else next((os.path.join('/dev', f) for f in sorted(os.listdir('/dev')) if f.startswith('cu.usbserial') and f.endswith('1')), None)
    out = args[-1]; frames = int(sys.argv[sys.argv.index('--frames') + 1]) if '--frames' in sys.argv else 1
    fd = open_port(port); P = Parser()
    def w(s): os.write(fd, s.encode())
    def pump(t):
        end = time.time() + t
        while time.time() < end:
            if select.select([fd], [], [], .05)[0]: P.feed(os.read(fd, 4096))
    w(']0'); pump(.1); w('?'); pump(.5)
    hello = re.search(r'#HELLO (\S+)', P.text); print('firmware', hello.group(1) if hello else 'no #HELLO (old firmware or other core)')
    P.text = ''; w('Q'); t0 = time.time()
    while '#SCR 115200' not in P.text and time.time() - t0 < 4: pump(.1)
    if '#SCR' not in P.text: w('v'); sys.exit('board did not start the screen stream; is an Open Pocket core running?')
    fb = [0] * (160 * 144); gbc = True; raw = False; dmg = [0xf8f8f8, 0xa8a8a8, 0x585858, 0x101010]; flags = 0; cells = None; seen = 0
    font = [int(x, 16) for x in open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'font8x8.hex')).read().split()]
    t0 = time.time()
    while seen < frames and time.time() - t0 < 60 + 20 * frames:
        pump(.2)
        for t, p in P.packets:
            if t == 'P' and len(p) == 14: gbc = bool(p[0]); raw = bool(p[1]); dmg = [p[2 + i * 3] << 16 | p[3 + i * 3] << 8 | p[4 + i * 3] for i in range(4)]
            elif t == 'O' and p:
                flags = p[0]
                if len(p) == 2017: cells = [p[1 + i * 2] | p[2 + i * 2] << 8 for i in range(1008)]
            elif t in 'GR':
                r = decode_row(t, p)
                if r: fb[r[0] * 160:r[0] * 160 + 160] = r[1]
            elif t == 'F': seen += 1
        P.packets.clear()
    w('v'); pump(.8); w('0'); pump(.1); os.close(fd)
    if not seen: sys.exit('no complete frame received')
    W, H, img = compose(fb, gbc, raw, dmg, flags, cells, font); png(out, W, H, img); print('saved', out, f'({seen} frame(s))')
main()
