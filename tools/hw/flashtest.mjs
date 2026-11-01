// Safe write/verify test on one free 4 KiB sector. Refuses to run if the sector is not blank.
import { createRequire } from 'node:module';
const { WebUSB } = createRequire(new URL('../../build/hw/', import.meta.url))('usb');
import { Jtag } from '../../docs/studio/jtag.mjs';
import { Gowin } from '../../docs/studio/gowin.mjs';
const ADDR = parseInt(process.argv[2] || '0x7FE000', 16);
const w = new WebUSB({ allowAllDevices: true });
const dev = (await w.getDevices()).find(d => d.vendorId === 0x0403 && d.productId === 0x6010);
const j = new Jtag(dev); await j.open(10e6);
const g = new Gowin(j); await g.detect(); await g.flashOpen();
const before = await g.flashRead(ADDR, 4096);
if (!before.every(b => b === 0xFF)) { console.log('sector not blank - abort'); await g.flashClose(); await j.close(); process.exit(2); }
const pat = Uint8Array.from({ length: 4096 }, (_, i) => (i * 7 + 13) & 255);
let t = Date.now();
await g.flashWrite(ADDR, pat, () => {}, { verify: true });
console.log('write+verify 4K ms', Date.now() - t);
// erase it again
await g.spi([0x06]); await g.spi([0x20, ADDR >> 16 & 255, ADDR >> 8 & 255, ADDR & 255]); await g.spiBusy();
console.log('blank again:', (await g.flashRead(ADDR, 4096)).every(b => b === 0xFF));
await g.flashClose(); await j.close();
