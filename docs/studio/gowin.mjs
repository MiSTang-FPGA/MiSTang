// Gowin GW2A(R)-18 programming over JTAG, ported from the open-source openFPGALoader (Apache-2.0/GPL-compat):
// SRAM load, external SPI flash erase/program/verify via the JTAG-to-SPI bridge (IR 0x16).
import { Jtag } from './jtag.mjs';
import { rev8 } from './fsparse.mjs';
const sleep = ms => new Promise(r => setTimeout(r, ms));
const NOOP = 0x02, ERASE_SRAM = 0x05, XFER_DONE = 0x09, READ_IDCODE = 0x11, INIT_ADDR = 0x12, CONFIG_ENABLE = 0x15,
  XFER_WRITE = 0x17, CONFIG_DISABLE = 0x3A, RELOAD = 0x3C, STATUS = 0x41, SPI_BRIDGE = 0x16;
export const ST = { CRC_ERROR: 1, MEMORY_ERASE: 1 << 5, EDIT: 1 << 7, DONE: 1 << 13 };
export const IDCODES = { 0x0000081b: 'GW2A(R)-18(C)', 0x0000281b: 'GW2A(R)-55(C)', 0x0100981b: 'GW1NR-9', 0x0100381b: 'GW1N-4' };

export class Gowin {
  constructor(jtag, log = () => {}) { this.j = jtag; this.log = log; }
  async cmd(c) { await this.j.shiftIR(c, 8); this.j.clocks(6); await this.j.flush(); }
  async reg32(c) {
    await this.cmd(c); const r = await this.j.shiftDR([0xFF, 0xFF, 0xFF, 0xFF], 32, { read: true });
    return (r[0] | r[1] << 8 | r[2] << 16 | r[3] << 24) >>> 0;
  }
  idcode() { return this.reg32(READ_IDCODE); }
  status() { return this.reg32(STATUS); }
  async poll(mask, value, tries = 20000) {
    for (let i = 0; i < tries; i++) { if (((await this.status()) & mask) === value) return true; }
    return false;
  }
  async detect() {
    const id = await this.idcode(); this.id = id;
    if (!IDCODES[id]) throw new Error(`Unexpected JTAG IDCODE 0x${id.toString(16)}. Is the Tang Nano 20K connected?`);
    return { id, name: IDCODES[id] };
  }
  async forceState() { // undocumented recovery used by openFPGALoader after a failed flash
    if (!((await this.status()) & ST.CRC_ERROR)) return;
    for (const c of [CONFIG_DISABLE, 0, READ_IDCODE]) await this.cmd(c);
    await this.status();
    for (const c of [CONFIG_DISABLE, 0]) await this.cmd(c);
    await this.status(); await this.idcode();
    await this.cmd(CONFIG_ENABLE); await this.reload(); await this.cmd(CONFIG_DISABLE); await this.cmd(NOOP);
    await this.idcode(); await this.cmd(NOOP); await this.idcode();
  }
  async reload() { await this.cmd(RELOAD); await this.cmd(NOOP); }
  async eraseSram() {
    await this.forceState();
    await this.cmd(CONFIG_ENABLE);
    if (!await this.poll(ST.EDIT, ST.EDIT)) throw new Error('config enable failed');
    await this.cmd(ERASE_SRAM); await this.cmd(NOOP);
    if (!await this.poll(ST.MEMORY_ERASE, ST.MEMORY_ERASE)) throw new Error('SRAM erase timed out');
    await this.cmd(XFER_DONE); await this.cmd(NOOP); await this.cmd(CONFIG_DISABLE); await this.cmd(NOOP);
    await this.poll(ST.EDIT, 0);
  }
  /** Load a bitstream into SRAM (volatile, runs immediately). `bytes` = sramBytes(fs). */
  async loadSram(bytes, checksum, onProgress = () => {}) {
    await this.eraseSram();
    await this.cmd(CONFIG_ENABLE); await this.cmd(INIT_ADDR); await this.cmd(XFER_WRITE);
    const j = this.j, STEP = 65536; // bytes per DR chunk
    j.goto('SHDR');
    for (let off = 0; off < bytes.length; off += STEP) {
      const part = bytes.subarray(off, Math.min(off + STEP, bytes.length)), last = off + STEP >= bytes.length;
      j.shift(part, part.length * 8, { exit: last });
      if (last) j.goto('RTI');
      await j.flush(); onProgress(Math.min(off + STEP, bytes.length) / bytes.length);
    }
    await this.cmd(0x0A);
    if (checksum !== null && checksum !== undefined) await j.shiftDR([checksum & 255, checksum >> 8 & 255, 0, 0], 32);
    await this.cmd(0x08); await this.cmd(CONFIG_DISABLE); await this.cmd(NOOP);
    const s = await this.status();
    if (!(s & ST.DONE)) throw new Error(`Bitstream did not start (status 0x${s.toString(16)}). Wrong device or corrupt file?`);
    return s;
  }
  // --- SPI flash through the JTAG bridge (GW2A: IR 0x16, shift in EXIT2_DR without capture)
  async spi(tx, readLen = 0) {
    const j = this.j, n = tx.length + readLen, total = readLen ? n + 1 : n;
    const out = new Uint8Array(total); for (let i = 0; i < tx.length; i++) out[i] = rev8(tx[i]);
    await this.cmd(SPI_BRIDGE);
    j.goto('E2DR');
    const rx = await j.shiftDR(out, total * 8, { read: !!readLen });
    if (!readLen) return null;
    const res = new Uint8Array(readLen);
    for (let i = 0; i < readLen; i++) { const k = tx.length + i; res[i] = rev8(rx[k] >> 1) | (rx[k + 1] & 1); }
    return res;
  }
  async spiBusy(timeout = 60000) {
    const t0 = Date.now();
    for (;;) {
      const s = (await this.spi([0x05], 1))[0];
      if (!(s & 1)) return;
      if (Date.now() - t0 > timeout) throw new Error('SPI flash busy timeout');
    }
  }
  async flashOpen() {
    await this.eraseSram();
    await this.j.setFreq(10e6);
    await this.spi([0x66]); await this.spi([0x99]); await sleep(2);
    await this.spi([0xAB]); await sleep(1);
    const id = await this.spi([0x9F], 3);
    if (id[0] === 0xFF || id[0] === 0) throw new Error('SPI flash not responding (ID ' + [...id].map(x => x.toString(16)).join(' ') + ')');
    return { manufacturer: id[0], type: id[1], capacity: 1 << id[2] };
  }
  async flashRead(addr, len) {
    const out = new Uint8Array(len), CH = 1024;
    for (let o = 0; o < len; o += CH) {
      const n = Math.min(CH, len - o), a = addr + o;
      out.set(await this.spi([0x03, a >> 16 & 255, a >> 8 & 255, a & 255], n), o);
    }
    return out;
  }
  async flashWrite(addr, data, onProgress = () => {}, { verify = true } = {}) {
    const SEC = 4096, end = addr + data.length;
    const a0 = addr & ~(SEC - 1);
    // erase
    for (let a = a0; a < end; a += SEC) {
      await this.spi([0x06]);
      await this.spi([0x20, a >> 16 & 255, a >> 8 & 255, a & 255]);
      await this.spiBusy();
      onProgress(0.3 * (a - a0 + SEC) / (end - a0));
    }
    // program, 256-byte pages, skipping erased (0xFF) pages
    for (let o = 0; o < data.length; o += 256) {
      const page = data.subarray(o, Math.min(o + 256, data.length));
      if (page.every(b => b === 0xFF)) continue;
      const a = addr + o;
      await this.spi([0x06]);
      await this.spi([0x02, a >> 16 & 255, a >> 8 & 255, a & 255, ...page]);
      await this.spiBusy();
      onProgress(0.3 + 0.5 * o / data.length);
    }
    if (verify) {
      for (let o = 0; o < data.length; o += 8192) {
        const n = Math.min(8192, data.length - o), got = await this.flashRead(addr + o, n);
        for (let i = 0; i < n; i++) if (got[i] !== data[o + i]) throw new Error(`Verify failed at 0x${(addr + o + i).toString(16)}`);
        onProgress(0.8 + 0.2 * (o + n) / data.length);
      }
    }
    onProgress(1);
  }
  async flashClose() { await this.reload(); }
}
