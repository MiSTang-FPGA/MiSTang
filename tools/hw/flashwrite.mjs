// Write files into the SPI flash and verify.  usage: node flashwrite.mjs <addr> <file> [<addr> <file> ...]
// .fs (ASCII bitstream) files are converted to binary first. DESTRUCTIVE: erases the 4 KiB sectors it writes. Dump first.
import { createRequire } from 'node:module'; import fs from 'node:fs';
const { WebUSB } = createRequire(new URL('../../build/hw/', import.meta.url))('usb');
import { Jtag } from '../../docs/studio/jtag.mjs'; import { Gowin } from '../../docs/studio/gowin.mjs';
const args = process.argv.slice(2);
if (!args.length || args.length % 2) { console.error('usage: flashwrite.mjs <addr> <file> ...'); process.exit(1); }
const load = f => {
  const raw = fs.readFileSync(f);
  if (f.endsWith('.fs')) {  // ASCII .fs: '/' comments, '0'/'1' lines
    const out = []; for (const l of raw.toString().split(/\r?\n/)) { if (!l || l[0] === '/') continue; for (let i = 0; i < l.length; i += 8) out.push(parseInt(l.substr(i, 8), 2)); }
    return Uint8Array.from(out);
  }
  return new Uint8Array(raw);
};
const w = new WebUSB({ allowAllDevices: true });
const dev = (await w.getDevices()).find(d => d.vendorId === 0x0403 && d.productId === 0x6010);
if (!dev) throw new Error('no FT2232');
const j = new Jtag(dev); await j.open(10e6); const g = new Gowin(j); await g.detect(); await g.flashOpen();
for (let i = 0; i < args.length; i += 2) {
  const addr = parseInt(args[i], 16), data = load(args[i + 1]);
  if (addr % 4096) throw new Error('address must be 4 KiB aligned');
  const t = Date.now(); let last = -1;
  await g.flashWrite(addr, data, (d, n) => { const p = Math.floor(100 * d / n / 10); if (p !== last) { last = p; process.stdout.write(`\r${args[i + 1]} @ ${args[i]}: ${p * 10}%`); } }, { verify: true });
  console.log(`\r${args[i + 1]} @ ${args[i]}: ${data.length} bytes written and verified in ${((Date.now() - t) / 1000).toFixed(1)} s`);
}
await g.flashClose(); await j.close();   // flashClose reloads the FPGA from flash
