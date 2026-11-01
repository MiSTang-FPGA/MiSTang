import test from 'node:test'; import assert from 'node:assert/strict';
import { tmsPath } from '../docs/studio/jtag.mjs';
import { parseBitstream, patchMultiboot, rev8 } from '../docs/studio/fsparse.mjs';
const step = { TLR: [0,1], RTI: [0,1] };
test('TAP paths reach target', () => {
  assert.deepEqual(tmsPath('RTI', 'SHDR'), [1, 0, 0]);
  assert.deepEqual(tmsPath('E1DR', 'RTI'), [1, 0]);
  assert.deepEqual(tmsPath('RTI', 'E2DR'), [1, 0, 1, 0, 1]);
  assert.deepEqual(tmsPath('TLR', 'RTI'), [0]);
});
test('rev8', () => { assert.equal(rev8(0x01), 0x80); assert.equal(rev8(0xA5), 0xA5); assert.equal(rev8(0x0F), 0xF0); });
function synth() { // FF.. A5C3, idcode, checksum, header(0x10), multiboot(0x52), end(0x3B)
  const b = [...Array(22).fill(0xFF), 0xA5, 0xC3, 0x06,0,0,0, 0,0,0x08,0x1B, 0x52,0,0,0, 0,0,0,0, 0x3B,0x80,0,2, 1,2,3,4];
  return Uint8Array.from(b);
}
test('parse + patch multiboot', () => {
  const bs = parseBitstream(synth());
  assert.equal(bs.hdr.idcode, 0x81b); assert.equal(bs.hdr.spiAddr, 0);
  const p = patchMultiboot(bs, 0x400000);
  assert.equal(parseBitstream(p).hdr.spiAddr, 0x400000);
  assert.equal(p.length, bs.bytes.length); // nothing else moves
  const diff = [...p].flatMap((v, i) => v !== bs.bytes[i] ? [i] : []);
  assert.deepEqual(diff, [bs.hdr.spiAddrOffset + 1]); // only 0x00->0x40 in byte 1 of 0x00400000
});
test('fs text equals bin', () => {
  const bin = synth(); const lines = ['// hdr', ...[...bin].reduce((a, v, i) => (i % 4 ? a[a.length-1] += v.toString(2).padStart(8,'0') : a.push(v.toString(2).padStart(8,'0')), a), [])];
  assert.deepEqual([...parseBitstream(new TextEncoder().encode(lines.join('\n') + '\n')).bytes], [...bin]);
});
