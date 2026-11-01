// Gowin bitstream handling (.fs ASCII or .bin raw), multiboot header patching.
// Everything is byte based: a .fs file is just the bit-text of the same byte stream as the .bin.
export const rev8 = b => { b = (b & 0xF0) >> 4 | (b & 0x0F) << 4; b = (b & 0xCC) >> 2 | (b & 0x33) << 2; return (b & 0xAA) >> 1 | (b & 0x55) << 1; };
const KEYLEN = { 0x06: 8, 0x0A: 4, 0x0B: 4, 0x10: 8, 0x12: 4, 0x51: 8, 0x52: 8, 0x3B: 4 };

function fsTextToBytes(text) {
  const out = [];
  for (const raw of text.split(/\r?\n/)) {
    if (!raw) continue;
    if (raw[0] === '/') continue;
    if (raw.length % 8) throw new Error('Corrupt .fs: line is not byte aligned');
    for (let i = 0; i < raw.length; i += 8) out.push(parseInt(raw.slice(i, i + 8), 2));
  }
  return Uint8Array.from(out);
}
const be32 = (u, o) => ((u[o] << 24) | (u[o + 1] << 16) | (u[o + 2] << 8) | u[o + 3]) >>> 0;

export function parseBitstream(input) {
  let bytes = input;
  if (input.length && (input[0] === 0x2F || input[0] === 0x30 || input[0] === 0x31)) // '/', '0', '1'
    bytes = fsTextToBytes(new TextDecoder().decode(input));
  let p = 0; while (p < bytes.length && bytes[p] === 0xFF) p++;
  if (bytes[p] !== 0xA5 || bytes[p + 1] !== 0xC3) throw new Error('Not a Gowin bitstream (preamble A5C3 missing)');
  p += 2;
  const hdr = { headerStart: p };
  for (;;) {
    const key = bytes[p] & 0x7F, len = KEYLEN[key];
    if (!len) throw new Error('Unknown header key 0x' + key.toString(16) + ' at ' + p);
    if (key === 0x06) hdr.idcode = be32(bytes, p + 4);
    if (key === 0x0A) hdr.checksum = (bytes[p + 2] << 8 | bytes[p + 3]) & 0xFFFF;
    if (key === 0x10) hdr.compressed = (bytes[p + 5] >> 5) & 1;
    if (key === 0x52) { hdr.spiAddr = be32(bytes, p + 4); hdr.spiAddrOffset = p + 4; }
    p += len;
    if (key === 0x3B) { hdr.dataStart = p; break; }
  }
  return { bytes, hdr };
}
/** Return a copy with the multiboot address (RECONFIG_N target) rewritten. */
export function patchMultiboot(bs, addr) {
  if (bs.hdr.spiAddrOffset === undefined) throw new Error('Bitstream has no multiboot header line (0x52)');
  const out = Uint8Array.from(bs.bytes), o = bs.hdr.spiAddrOffset;
  out[o] = addr >>> 24; out[o + 1] = addr >>> 16 & 255; out[o + 2] = addr >>> 8 & 255; out[o + 3] = addr & 255;
  return out;
}
export const sramBytes = bytes => Uint8Array.from(bytes, rev8);
