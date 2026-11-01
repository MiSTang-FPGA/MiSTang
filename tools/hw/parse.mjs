import fs from 'node:fs';
import { parseBitstream } from '../../docs/studio/fsparse.mjs';
const b = parseBitstream(new Uint8Array(fs.readFileSync(process.argv[2])));
console.log(b.bytes.length, b.hdr, b.hdr.idcode.toString(16), b.hdr.spiAddr?.toString(16));
