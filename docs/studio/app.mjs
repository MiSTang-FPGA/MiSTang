import { Jtag, VID, PID } from './jtag.mjs';
import { Gowin } from './gowin.mjs';
import { parseBitstream, patchMultiboot, sramBytes } from './fsparse.mjs';
const $ = s => document.querySelector(s), $$ = s => [...document.querySelectorAll(s)];
const hex = n => '0x' + n.toString(16).padStart(6, '0');
const SLOT_A = 0x400000, LAUNCHER = 0x000000;
let dev = null, jtag = null, gw = null, bs = null, fileName = '', busy = false;

// ---- log / status
function log(m) { const b = $('#logbox'); b.textContent += `[${new Date().toLocaleTimeString()}] ${m}\n`; b.scrollTop = b.scrollHeight; }
function status(m, cls = '') { const s = $('#status'); s.textContent = m; s.className = 'mono status ' + cls; log(m); }
const progress = f => { $('#bar').style.width = (f * 100).toFixed(1) + '%'; };
$('#logClear').onclick = () => { $('#logbox').textContent = ''; };

// ---- tabs
for (const t of $$('.tab')) t.onclick = () => {
  $$('.tab').forEach(x => x.classList.toggle('on', x === t));
  $$('.pane').forEach(p => { p.hidden = p.id !== t.dataset.t; });
  if (t.dataset.t === 'capture') listCams();
};
$('#support').textContent = ('usb' in navigator ? '' : 'WebUSB not available — use Chrome or Edge. ') + (isSecureContext ? '' : 'Needs HTTPS or localhost.');

// ---- board connection
function setState(ok, text) { $('#boardState').classList.toggle('ok', ok); $('#boardState span').textContent = text; $('#connect').textContent = ok ? 'Disconnect' : 'Connect board'; }
function refresh() { const on = !!gw && !busy; $('#runSram').disabled = !(on && bs); $('#writeFlash').disabled = !(on && bs); $('#reload').disabled = !on; $('#flashId').disabled = !on; }
async function connect() {
  if (gw) { await jtag.close().catch(() => {}); jtag = gw = dev = null; setState(false, 'No board'); refresh(); return; }
  dev = await navigator.usb.requestDevice({ filters: [{ vendorId: VID, productId: PID }] });
  jtag = new Jtag(dev); await jtag.open(6e6); gw = new Gowin(jtag, log);
  const d = await gw.detect(); log(`JTAG IDCODE 0x${d.id.toString(16)} ${d.name}`);
  setState(true, d.name + ' · connected'); refresh();
}
$('#connect').onclick = () => guard(connect);
async function guard(fn) {
  if (busy) return; busy = true; refresh(); progress(0);
  try { await fn(); } catch (e) { status(e.message || String(e), 'err'); if (/access|claim|denied|LIBUSB/i.test(String(e.message))) log('Hint: on Windows install WinUSB for interface 0 with Zadig; on Linux add a udev rule for 0403:6010.'); }
  finally { busy = false; refresh(); }
}
navigator.usb?.addEventListener('disconnect', e => { if (e.device === dev) { jtag = gw = dev = null; setState(false, 'No board'); refresh(); log('Board unplugged'); } });

// ---- bitstream file
async function takeFile(f) {
  try {
    bs = parseBitstream(new Uint8Array(await f.arrayBuffer())); fileName = f.name;
    const h = bs.hdr, ok = h.idcode === 0x0000081b;
    $('#info').hidden = false;
    $('#info').innerHTML = [`<span>${f.name}</span>`, `<span>${(bs.bytes.length / 1024).toFixed(0)} KiB</span>`, `<span class="${ok ? '' : 'warn'}">IDCODE ${h.idcode?.toString(16)}${ok ? ' ✓ GW2A-18' : ' ✗ not GW2A-18'}</span>`,
      `<span>${h.compressed ? 'compressed' : 'uncompressed'}</span>`, `<span>multiboot → ${hex(h.spiAddr ?? 0)}</span>`].join('');
    if (!$('#coreId').value) $('#coreId').value = f.name.replace(/\.(fs|bin)$/i, '').toLowerCase().replace(/[^a-z0-9]+/g, '-');
    status(`Loaded ${f.name}`); refresh(); $('#sdAdd').disabled = !sdRoot;
  } catch (e) { bs = null; $('#info').hidden = true; status(e.message, 'err'); refresh(); }
}
$('#file').onchange = e => e.target.files[0] && takeFile(e.target.files[0]);
const drop = $('#drop');
['dragover', 'dragenter'].forEach(ev => drop.addEventListener(ev, e => { e.preventDefault(); drop.classList.add('over'); }));
['dragleave', 'drop'].forEach(ev => drop.addEventListener(ev, e => { e.preventDefault(); drop.classList.remove('over'); }));
drop.addEventListener('drop', e => e.dataTransfer.files[0] && takeFile(e.dataTransfer.files[0]));

$('#runSram').onclick = () => guard(async () => {
  status('Erasing SRAM and loading…'); const t = performance.now();
  await gw.loadSram(sramBytes(bs.bytes), bs.hdr.checksum ?? null, progress);
  status(`Running. Loaded in ${((performance.now() - t) / 1000).toFixed(1)} s (SRAM, volatile).`, 'ok');
});
$('#target').onchange = () => { $('#customWrap').hidden = $('#target').value !== 'custom'; };
const addrOf = () => $('#target').value === 'custom' ? parseInt($('#custom').value, 16) : parseInt($('#target').value, 16);
$('#writeFlash').onclick = () => guard(async () => {
  const addr = addrOf(); if (!Number.isFinite(addr) || addr % 4096) throw new Error('Offset must be a multiple of 4 KiB');
  let bytes = bs.bytes;
  if ($('#mb').value === 'auto') {
    const target = addr === LAUNCHER ? SLOT_A : LAUNCHER;
    if (bs.hdr.spiAddrOffset !== undefined) { bytes = patchMultiboot(bs, target); log(`Patched multiboot header: ${hex(bs.hdr.spiAddr)} → ${hex(target)}`); }
  }
  if (addr + bytes.length > 0x7FF000) throw new Error('Does not fit in flash');
  status('Opening SPI flash…'); const f = await gw.flashOpen(); log(`Flash: ${f.manufacturer.toString(16)} ${f.type.toString(16)}, ${f.capacity >> 20} MiB`);
  const t = performance.now();
  await gw.flashWrite(addr, bytes, p => { progress(p); }, { verify: $('#verify').checked });
  await gw.flashClose();
  status(`Wrote ${(bytes.length / 1024).toFixed(0)} KiB at ${hex(addr)}${$('#verify').checked ? ' (verified)' : ''} in ${((performance.now() - t) / 1000).toFixed(0)} s. FPGA reloaded from flash.`, 'ok');
});
$('#rawFile').onchange = e => guard(async () => {
  const f = e.target.files[0]; if (!f) return; const addr = parseInt($('#rawOff').value, 16); if (addr % 4096) throw new Error('Offset must be a multiple of 4 KiB');
  const data = new Uint8Array(await f.arrayBuffer()); await gw.flashOpen();
  await gw.flashWrite(addr, data, progress); await gw.flashClose(); status(`Wrote ${f.name} (${data.length} B) at ${hex(addr)}.`, 'ok'); e.target.value = '';
});
$('#reload').onclick = () => guard(async () => { await gw.reload(); status('RELOAD sent — FPGA boots from flash.', 'ok'); });
$('#flashId').onclick = () => guard(async () => { const f = await gw.flashOpen(); await gw.flashClose(); status(`SPI flash: manufacturer 0x${f.manufacturer.toString(16)}, type 0x${f.type.toString(16)}, ${f.capacity >> 20} MiB`, 'ok'); });

// ---- capture (UVC via getUserMedia)
let stream = null, rec = null, chunks = [];
async function listCams() {
  if (!navigator.mediaDevices) return;
  try { const tmp = await navigator.mediaDevices.getUserMedia({ video: true }); tmp.getTracks().forEach(t => t.stop()); } catch {}
  const devs = (await navigator.mediaDevices.enumerateDevices()).filter(d => d.kind === 'videoinput');
  $('#cams').innerHTML = devs.map(d => `<option value="${d.deviceId}">${d.label || 'Camera'}</option>`).join('') || '<option value="">No video devices</option>';
}
$('#camStart').onclick = async () => {
  if (stream) { stream.getTracks().forEach(t => t.stop()); stream = null; $('#video').srcObject = null; $('#camStart').textContent = 'Start'; ['camShot', 'camRec', 'camFs'].forEach(i => $('#' + i).disabled = true); $('#camEmpty').hidden = false; return; }
  try {
    stream = await navigator.mediaDevices.getUserMedia({ video: { deviceId: $('#cams').value ? { exact: $('#cams').value } : undefined, width: { ideal: 1920 }, height: { ideal: 1080 }, frameRate: { ideal: 60 } }, audio: $('#audio').checked });
    const v = $('#video'); v.srcObject = stream; await v.play(); v.muted = false; $('#camEmpty').hidden = true; $('#camStart').textContent = 'Stop';
    ['camShot', 'camRec', 'camFs'].forEach(i => $('#' + i).disabled = false);
    const s = stream.getVideoTracks()[0].getSettings(); $('#camInfo').textContent = `${s.width}×${s.height} @ ${Math.round(s.frameRate || 0)} fps`;
  } catch (e) { status('Capture: ' + e.message, 'err'); }
};
$('#crt').onchange = e => $('#stage').classList.toggle('crt', e.target.checked);
$('#scale').onchange = e => $('#stage').classList.toggle('int', e.target.value === 'int');
$('#camFs').onclick = () => $('#stage').requestFullscreen?.();
$('#camShot').onclick = () => {
  const v = $('#video'), c = document.createElement('canvas'); c.width = v.videoWidth; c.height = v.videoHeight; c.getContext('2d').drawImage(v, 0, 0);
  c.toBlob(b => download(b, `mistang-${stamp()}.png`));
};
$('#camRec').onclick = () => {
  if (rec) { rec.stop(); return; }
  const mime = ['video/webm;codecs=vp9,opus', 'video/webm;codecs=vp8,opus', 'video/webm'].find(m => MediaRecorder.isTypeSupported(m));
  rec = new MediaRecorder(stream, { mimeType: mime, videoBitsPerSecond: 12e6 }); chunks = [];
  rec.ondataavailable = e => e.data.size && chunks.push(e.data);
  rec.onstop = () => { download(new Blob(chunks, { type: 'video/webm' }), `mistang-${stamp()}.webm`); rec = null; $('#camRec').textContent = 'Record'; };
  rec.start(1000); $('#camRec').textContent = 'Stop rec';
};
const stamp = () => new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
function download(blob, name) { const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = name; a.click(); setTimeout(() => URL.revokeObjectURL(a.href), 5000); }

// ---- remote (Web Serial, interface B)
let port = null, writer = null;
$('#serConnect').onclick = async () => {
  try {
    if (port) { writer?.releaseLock(); await port.close(); port = null; $('#serConnect').textContent = 'Connect serial'; $('#serState').textContent = 'disconnected'; return; }
    port = await navigator.serial.requestPort({ filters: [{ usbVendorId: VID, usbProductId: PID }] });
    await port.open({ baudRate: 115200 }); writer = port.writable.getWriter();
    $('#serConnect').textContent = 'Disconnect'; $('#serState').textContent = 'connected 115200';
    (async () => { const r = port.readable.getReader(); const dec = new TextDecoder(); try { for (;;) { const { value, done } = await r.read(); if (done) break; log('[uart] ' + dec.decode(value).trimEnd()); } } catch {} r.releaseLock(); })();
  } catch (e) { status('Serial: ' + e.message, 'err'); port = null; }
};
const send = s => writer?.write(new TextEncoder().encode(s)).catch(() => {});
for (const b of $$('#pad button')) {
  const k = b.dataset.k, down = () => { b.classList.add('down'); send(k); }, up = () => { b.classList.remove('down'); send(k.toLowerCase()); };
  b.onpointerdown = e => { e.preventDefault(); b.setPointerCapture(e.pointerId); down(); }; b.onpointerup = up; b.onpointercancel = up;
}
const KEYS = { ArrowUp: 'U', ArrowDown: 'D', ArrowLeft: 'L', ArrowRight: 'R', x: 'A', z: 'B', Enter: 'T', Backspace: 'S', m: 'M' };
addEventListener('keydown', e => { if ($('#remote').hidden || e.repeat || /INPUT|SELECT/.test(e.target.tagName)) return; const k = KEYS[e.key]; if (k) { e.preventDefault(); send(k); $(`[data-k=${k}]`)?.classList.add('down'); } });
addEventListener('keyup', e => { const k = KEYS[e.key]; if (k && !$('#remote').hidden) { send(k.toLowerCase()); $(`[data-k=${k}]`)?.classList.remove('down'); } });

// ---- SD card preparation
let sdRoot = null;
async function dir(parent, name) { return parent.getDirectoryHandle(name, { create: true }); }
$('#sdPick').onclick = async () => {
  try { sdRoot = await showDirectoryPicker({ mode: 'readwrite' }); $('#sdName').textContent = sdRoot.name; $('#sdLayout').disabled = false; $('#sdAdd').disabled = !bs; }
  catch (e) { if (e.name !== 'AbortError') status('SD: ' + e.message, 'err'); }
};
$('#sdLayout').onclick = async () => {
  const root = await dir(sdRoot, 'MiSTang');
  for (const n of ['cores', 'games', 'saves', 'bios', 'screens']) await dir(root, n);
  for (const n of ['nes', 'snes', 'gb', 'gbc', 'sms', 'gg', 'pce', 'md', 'msx', 'ws']) await dir(await dir(root, 'games'), n);
  status('SD layout created.', 'ok');
};
$('#sdAdd').onclick = async () => {
  try {
    const id = ($('#coreId').value || 'core').replace(/[^a-z0-9-]/gi, '-').toLowerCase();
    const bytes = bs.hdr.spiAddrOffset !== undefined ? patchMultiboot(bs, LAUNCHER) : bs.bytes;
    const cores = await dir(await dir(sdRoot, 'MiSTang'), 'cores');
    const w = await (await cores.getFileHandle(id + '.bin', { create: true })).createWritable(); await w.write(bytes); await w.close();
    const meta = { id, name: $('#coreName').value || id, ext: ($('#coreExt').value || '').split(',').map(s => s.trim()).filter(Boolean), size: bytes.length, multiboot: 0, built: new Date().toISOString() };
    const m = await (await cores.getFileHandle(id + '.json', { create: true })).createWritable(); await m.write(JSON.stringify(meta, null, 1)); await m.close();
    status(`Wrote /MiSTang/cores/${id}.bin (${(bytes.length / 1024).toFixed(0)} KiB), multiboot → launcher.`, 'ok');
  } catch (e) { status('SD: ' + e.message, 'err'); }
};
refresh();
