// FTDI FT2232 (Tang Nano 20K "20K's FRIEND" = Sipeed debugger) JTAG over WebUSB/MPSSE.
// The `dev` object only needs the WebUSB API surface, so the same code runs in Chrome and in
// node (tools/node-usb-adapter.mjs) for hardware tests.
export const VID = 0x0403, PID = 0x6010;
const sleep = ms => new Promise(r => setTimeout(r, ms));

// --- TAP state machine ------------------------------------------------------------------
const T = { // state: [next on TMS=0, next on TMS=1]
  TLR: ['RTI', 'TLR'], RTI: ['RTI', 'SDR'],
  SDR: ['CDR', 'SIR'], CDR: ['SHDR', 'E1DR'], SHDR: ['SHDR', 'E1DR'], E1DR: ['PDR', 'UDR'],
  PDR: ['PDR', 'E2DR'], E2DR: ['SHDR', 'UDR'], UDR: ['RTI', 'SDR'],
  SIR: ['CIR', 'TLR'], CIR: ['SHIR', 'E1IR'], SHIR: ['SHIR', 'E1IR'], E1IR: ['PIR', 'UIR'],
  PIR: ['PIR', 'E2IR'], E2IR: ['SHIR', 'UIR'], UIR: ['RTI', 'SDR'],
};
export function tmsPath(from, to) {
  if (from === to) return [];
  const q = [[from, []]], seen = new Set([from]);
  while (q.length) {
    const [s, p] = q.shift();
    for (const b of [0, 1]) {
      const n = T[s][b];
      if (seen.has(n)) continue;
      if (n === to) return [...p, b];
      seen.add(n); q.push([n, [...p, b]]);
    }
  }
  throw new Error(`no TAP path ${from}->${to}`);
}

// --- MPSSE ---------------------------------------------------------------------------------
export class Jtag {
  constructor(dev, { epIn = 1, epOut = 2, iface = 0, packet = 512 } = {}) {
    this.dev = dev; this.epIn = epIn; this.epOut = epOut; this.iface = iface; this.packet = packet;
    this.buf = []; this.state = 'TLR'; this.freq = 0; this.expect = 0;
  }
  async open(freq = 6e6) {
    const d = this.dev;
    if (!d.opened) await d.open();
    if (d.configuration === null || d.configuration === undefined) await d.selectConfiguration(1);
    await d.claimInterface(this.iface);
    const idx = this.iface + 1;
    const ctl = (request, value) => d.controlTransferOut({ requestType: 'vendor', recipient: 'device', request, value, index: idx }, new Uint8Array(0));
    await ctl(0x00, 0);                 // reset
    await ctl(0x0B, 0x0000);            // bitmode reset
    await ctl(0x09, 1);                 // latency timer 1 ms
    await ctl(0x0B, 0x0200 | 0xFB);     // MPSSE mode, direction mask
    await ctl(0x00, 1); await ctl(0x00, 2); // purge rx/tx
    this.buf = []; this.expect = 0;
    // sync: bad command must echo 0xFA 0xAA
    this.put(0xAA); await this.flushRaw();
    const r = await this.readRaw(2).catch(() => null);
    if (!r || r[0] !== 0xFA || r[1] !== 0xAA) throw new Error('MPSSE sync failed');
    this.put(0x8A, 0x97, 0x8D);         // clk /1 (60 MHz), no adaptive, no 3-phase
    this.put(0x80, 0x08, 0x0B);         // low byte: TMS=1 idle, TCK/TDI/TMS out
    this.put(0x82, 0x00, 0x00);
    this.put(0x85);                     // loopback off
    await this.setFreq(freq);
    await this.reset();
    return this;
  }
  async close() { try { await this.dev.releaseInterface(this.iface); } catch {} try { await this.dev.close(); } catch {} }
  put(...b) { for (const x of b) this.buf.push(x); }
  async setFreq(hz) {
    const div = Math.max(0, Math.round(60e6 / (2 * hz)) - 1);
    this.put(0x86, div & 255, div >> 8); await this.flush();
    this.freq = 60e6 / (2 * (div + 1));
  }
  async flushRaw() {
    if (!this.buf.length) return;
    const data = Uint8Array.from(this.buf); this.buf = [];
    // chunk to keep USB transfers sane
    for (let i = 0; i < data.length; i += 16384) await this.dev.transferOut(this.epOut, data.subarray(i, i + 16384));
  }
  async flush() {
    this.put(0x87);                     // send immediate
    await this.flushRaw();
    if (this.expect) { const r = await this.readRaw(this.expect); this.expect = 0; return r; }
    return new Uint8Array(0);
  }
  async readRaw(n, timeout = 3000) {
    const out = new Uint8Array(n); let got = 0; const t0 = Date.now();
    while (got < n) {
      const res = await this.dev.transferIn(this.epIn, this.packet);
      const v = new Uint8Array(res.data.buffer, res.data.byteOffset, res.data.byteLength);
      for (let p = 0; p < v.length; p += this.packet) {
        const chunk = v.subarray(p + 2, Math.min(p + this.packet, v.length)); // 2 modem status bytes
        const take = Math.min(chunk.length, n - got); out.set(chunk.subarray(0, take), got); got += take;
      }
      if (got < n && Date.now() - t0 > timeout) throw new Error('JTAG read timeout');
    }
    return out;
  }
  // --- low-level TAP moves
  tmsBits(bits, tdi = 0) {
    for (let i = 0; i < bits.length; i += 7) {
      const part = bits.slice(i, i + 7); let v = 0;
      part.forEach((b, k) => { v |= b << k; });
      this.put(0x4B, part.length - 1, v | (tdi << 7));
    }
  }
  goto(to) {
    const path = tmsPath(this.state, to); if (path.length) this.tmsBits(path); this.state = to;
  }
  async reset() { this.tmsBits([1, 1, 1, 1, 1, 0]); this.state = 'RTI'; await this.flush(); }
  setState(s) { this.goto(s); }
  clocks(n) { // idle clocks with TMS=0 (the Sipeed FT2232 firmware lacks 0x8E/0x8F, so use TMS-only shifts)
    while (n > 0) { const k = Math.min(7, n); this.put(0x4B, k - 1, 0); n -= k; }
  }
  // Shift `nbits` of `data` (LSB-first per byte). exit=true: last bit carries TMS=1 -> E1.
  // Returns captured TDO bytes when read=true (queued; use flush()).
  shift(data, nbits, { read = false, exit = true } = {}) {
    const shiftState = this.state; // SHDR or SHIR
    let bits = nbits, at = 0;
    const lastBit = exit ? 1 : 0;
    const body = bits - lastBit; // bits sent with TMS=0
    const nbytes = body >> 3, rem = body & 7;
    let readBytes = 0;
    if (nbytes) {
      const cmd = read ? 0x39 : 0x19;
      // MPSSE max 65536 bytes per command
      for (let off = 0; off < nbytes; off += 65536) {
        const n = Math.min(65536, nbytes - off);
        this.put(cmd, (n - 1) & 255, (n - 1) >> 8);
        for (let i = 0; i < n; i++) this.buf.push(data ? data[at + off + i] : 0xFF);
        if (read) readBytes += n;
      }
      at += nbytes;
    }
    if (rem) {
      this.put(read ? 0x3B : 0x1B, rem - 1, data ? data[at] & ((1 << rem) - 1) : 0xFF); at++;
      if (read) readBytes += 1;
    }
    if (exit) {
      const byte = data ? data[nbits - 1 >> 3] : 0xFF; const bit = (byte >> ((nbits - 1) & 7)) & 1;
      this.put(read ? 0x6B : 0x4B, 0, 1 | (bit << 7));
      if (read) readBytes += 1;
      this.state = shiftState === 'SHIR' ? 'E1IR' : 'E1DR';
    }
    if (read) this.expect += readBytes;
    this._rd = read ? { nbits, body, nbytes, rem, exit } : null;
  }
  // assemble result of a read shift into nbits LSB-first bytes
  static assemble(raw, info) {
    const out = new Uint8Array((info.nbits + 7) >> 3); let p = 0;
    for (let i = 0; i < info.nbytes; i++) out[i] = raw[p++];
    if (info.rem) out[info.nbytes] = raw[p++] >> (8 - info.rem);
    if (info.exit) { const b = raw[p++] >> 7; out[(info.nbits - 1) >> 3] |= b << ((info.nbits - 1) & 7); }
    return out;
  }
  async shiftIR(value, bits = 8, then = 'RTI') {
    this.goto('SHIR'); this.shift([value], bits, { exit: true }); this.goto(then); await this.flush();
  }
  async shiftDR(data, nbits, { read = false, then = 'RTI', exit = true } = {}) {
    this.goto('SHDR'); this.shift(data, nbits, { read, exit }); const info = this._rd;
    if (exit) this.goto(then);
    const raw = await this.flush();
    return read ? Jtag.assemble(raw, info) : null;
  }
}
