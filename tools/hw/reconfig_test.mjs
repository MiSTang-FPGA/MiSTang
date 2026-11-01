// RECONFIG_N multiboot test. B -> flash @ADDR; A (multiboot=ADDR) -> SRAM; A pulls pin 9 low after ~5 s;
// if the FPGA reloads from ADDR we see B's USERCODE.   usage: node reconfig_test.mjs a.fs b.fs 0x4A0000 [--write]
import { createRequire } from 'node:module'; import fs from 'node:fs';
const { WebUSB } = createRequire(new URL('../../build/hw/', import.meta.url))('usb');
import { Jtag } from '../../docs/studio/jtag.mjs'; import { Gowin } from '../../docs/studio/gowin.mjs';
import { parseBitstream, sramBytes } from '../../docs/studio/fsparse.mjs';
const [fa, fb, addrS] = process.argv.slice(2), ADDR = parseInt(addrS, 16), WRITE = process.argv.includes('--write');
const A = parseBitstream(new Uint8Array(fs.readFileSync(fa))), B = parseBitstream(new Uint8Array(fs.readFileSync(fb)));
const w = new WebUSB({ allowAllDevices: true });
const dev = (await w.getDevices()).find(d => d.vendorId === 0x0403 && d.productId === 0x6010);
const j = new Jtag(dev); await j.open(10e6); const g = new Gowin(j); await g.detect();
const hex = n => '0x' + n.toString(16);
const sleep = ms => new Promise(r => setTimeout(r, ms));
await g.flashOpen();
const region = await g.flashRead(ADDR, (B.bytes.length + 4095) & ~4095);
const blank = region.every(b => b === 0xFF);
console.log('region', hex(ADDR), 'len', region.length, 'blank:', blank);
if (!blank) { console.log('not blank - abort'); await g.flashClose(); await j.close(); process.exit(2); }
if (!WRITE) { await g.flashClose(); await j.close(); process.exit(0); }
await g.flashWrite(ADDR, B.bytes, () => {}, { verify: true }); console.log('B written+verified @', hex(ADDR));
await g.loadSram(sramBytes(A.bytes), null); console.log('A loaded to SRAM');
const uc = async () => hex(await g.reg32(0x13)), st = async () => hex(await g.status());
console.log('after load  usercode', await uc(), 'status', await st());
for (let i = 1; i <= 10; i++) { await sleep(1000); console.log(`t+${i}s usercode`, await uc(), 'status', await st()); }
await j.close();
