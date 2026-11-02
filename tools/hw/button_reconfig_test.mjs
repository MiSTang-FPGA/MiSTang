// Core return-to-launcher test with REAL buttons. Core (multiboot patched to ADDR) -> SRAM, stub B -> flash @ADDR.
// Hold S1+S2 ~2 s within the window: USERCODE must change from the core's to B's. Cleans up the flash afterwards.
// usage: node button_reconfig_test.mjs core.fs b.fs 0x4F0000 [seconds]
import { createRequire } from 'node:module'; import fs from 'node:fs';
const { WebUSB } = createRequire(new URL('../../build/hw/', import.meta.url))('usb');
import { Jtag } from '../../docs/studio/jtag.mjs'; import { Gowin } from '../../docs/studio/gowin.mjs';
import { parseBitstream, patchMultiboot, sramBytes } from '../../docs/studio/fsparse.mjs';
const [fc, fb, addrS, secS] = process.argv.slice(2), ADDR = parseInt(addrS, 16), WIN = +(secS || 120);
const C = parseBitstream(new Uint8Array(fs.readFileSync(fc))), B = parseBitstream(new Uint8Array(fs.readFileSync(fb)));
const coreBytes = patchMultiboot(C, ADDR);
const w = new WebUSB({ allowAllDevices: true });
const dev = (await w.getDevices()).find(d => d.vendorId === 0x0403 && d.productId === 0x6010);
const j = new Jtag(dev); await j.open(10e6); const g = new Gowin(j); await g.detect();
const hex = n => '0x' + n.toString(16), sleep = ms => new Promise(r => setTimeout(r, ms));
const len = (B.bytes.length + 4095) & ~4095;
let dirty = false;
try {
  await g.flashOpen();
  if (!(await g.flashRead(ADDR, len)).every(b => b === 0xFF)) throw new Error('region not blank');
  dirty = true; await g.flashWrite(ADDR, B.bytes, () => {}, { verify: true });
  await g.loadSram(sramBytes(coreBytes), null);
  const base = await g.reg32(0x13); console.log('core running, usercode', hex(base), '- HOLD S1+S2 for 2 s now (window', WIN, 's)');
  let changed = null;
  for (let t = 0; t < WIN * 2; t++) { await sleep(500); const u = await g.reg32(0x13); if (u !== base) { // 0x0 = read during reconfiguration; wait for the new design to settle
      let v = u; for (let k = 0; k < 20 && (v === 0 || v === base); k++) { await sleep(500); v = await g.reg32(0x13); }
      for (let k = 0; k < 6; k++) { console.log(`  +${k * 0.5}s after reload: status ${hex(await g.status())} usercode ${hex(await g.reg32(0x13))}`); await sleep(500); }
      changed = [t / 2, v]; break; } }
  console.log(changed ? `RELOADED at +${changed[0]}s, usercode ${hex(changed[1])} (stub B expected 0xfd4b)` : 'NO RELOAD within window');
} finally {
  if (dirty) { await g.flashOpen(); for (let a = ADDR; a < ADDR + len; a += 4096) { await g.spi([0x06]); await g.spi([0x20, a >> 16 & 255, a >> 8 & 255, a & 255]); await g.spiBusy(); }
    console.log('flash region restored blank:', (await g.flashRead(ADDR, len)).every(b => b === 0xFF)); }
  // leave a bitstream with multiboot=0 loaded before RELOAD, so the reload cannot target the (now blank) test region
  await g.loadSram(sramBytes(B.bytes), null).catch(e => console.log('cleanup load failed', e.message));
  await g.flashClose(); await j.close();
}
