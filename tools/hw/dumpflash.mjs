// Read-only: dump the whole 8 MiB SPI flash to a file.   usage: node dumpflash.mjs out.bin
import { createRequire } from 'node:module'; import fs from 'node:fs';
const { WebUSB } = createRequire(new URL('../../build/hw/', import.meta.url))('usb');
import { Jtag } from '../../docs/studio/jtag.mjs'; import { Gowin } from '../../docs/studio/gowin.mjs';
const w = new WebUSB({ allowAllDevices: true });
const dev = (await w.getDevices()).find(d => d.vendorId === 0x0403 && d.productId === 0x6010);
const j = new Jtag(dev); await j.open(15e6); const g = new Gowin(j); await g.detect(); const f = await g.flashOpen();
const out = new Uint8Array(f.capacity);
for (let a = 0; a < out.length; a += 0x10000) out.set(await g.flashRead(a, 0x10000), a);
fs.writeFileSync(process.argv[2], out); console.log('dumped', out.length, 'bytes');
await g.flashClose(); await j.close();
