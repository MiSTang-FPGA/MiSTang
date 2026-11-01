// Read the whole flash and print blank 4 KiB runs (>= 64 KiB). Read-only.
import { createRequire } from 'node:module';
const { WebUSB } = createRequire(new URL('../../build/hw/', import.meta.url))('usb');
import { Jtag } from '../../docs/studio/jtag.mjs'; import { Gowin } from '../../docs/studio/gowin.mjs';
const w = new WebUSB({ allowAllDevices: true });
const dev = (await w.getDevices()).find(d => d.vendorId === 0x0403 && d.productId === 0x6010);
const j = new Jtag(dev); await j.open(15e6); const g = new Gowin(j); await g.detect(); await g.flashOpen();
const runs = []; let start = null;
for (let a = 0; a < 0x800000; a += 0x10000) {
  const d = await g.flashRead(a, 0x10000);
  for (let s = 0; s < 16; s++) {
    const blank = d.subarray(s * 4096, s * 4096 + 4096).every(b => b === 0xFF), addr = a + s * 4096;
    if (blank && start === null) start = addr;
    if (!blank && start !== null) { runs.push([start, addr]); start = null; }
  }
}
if (start !== null) runs.push([start, 0x800000]);
for (const [s, e] of runs) if (e - s >= 0x10000) console.log('blank', '0x' + s.toString(16), '-', '0x' + e.toString(16), ((e - s) / 1024) + ' KiB');
await g.flashClose(); await j.close();
