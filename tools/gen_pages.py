#!/usr/bin/env python3
"""Generates docs/cores.html and docs/how.html, re-using nav + footer of docs/index.html."""
import re, pathlib
D = pathlib.Path(__file__).resolve().parent.parent / 'docs'
idx = (D/'index.html').read_text()
nav = re.search(r'<nav class="top">.*?</nav>', idx, re.S).group(0)
foot = re.search(r'<footer>.*?</footer>', idx, re.S).group(0)
def on(nav, key):
    return re.sub(r'(<a class=")("\s+href="%s")' % key, r'\1on\2', nav)
def page(name, title, key, body, head=''):
    n = on(nav, key)
    (D/name).write_text(f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title}</title><link rel="stylesheet" href="assets/site.css">{head}</head><body>{n}{foot}</body></html>'''.replace('</footer>', '</footer>',1).replace(foot, body+foot) if False else
    f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title}</title><link rel="stylesheet" href="assets/site.css">{head}</head><body>{n}{body}{foot}</body></html>''')

page('cores.html', 'MiSTang — core catalog', 'cores.html', '''
<section style="padding-top:48px"><div class="wrap"><div class="eyebrow">Catalog</div><h2>Which MiSTer cores can live on 20 736 LUT4?</h2>
<p class="sub">Sorted by honest feasibility, not by hype. “Proven” means someone has already booted it on a Tang Nano 20K. Everything else is an estimate from system class and the MiSTer docs; click through to the source repo.</p>
<div id="tiers" style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px"></div>
<div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:22px"><input id="q" placeholder="Search 230 cores — nes, pac-man, amstrad, dvd…" style="flex:1;min-width:240px;padding:13px 18px;border-radius:999px;border:1px solid var(--line);background:var(--card);color:var(--ink);font:inherit"><select id="cat" style="padding:0 16px;border-radius:999px;border:1px solid var(--line);background:var(--card);color:var(--ink)"><option value="">All types</option><option>console</option><option>computer</option><option>arcade</option><option>other</option></select></div>
<div id="count" class="mono" style="color:var(--mute);font-size:13px;margin-bottom:14px"></div>
<div id="grid" style="display:grid;grid-template-columns:repeat(auto-fill,minmax(270px,1fr));gap:12px"></div></div></section>
<style>.core{border:1px solid var(--line);background:var(--card);border-radius:14px;padding:16px;display:flex;flex-direction:column;gap:6px;transition:.15s}.core:hover{border-color:#3a4258;transform:translateY(-2px)}.core b{font-size:16px}.core small{color:var(--dim);font-size:13px;flex:1}.core .m{display:flex;justify-content:space-between;align-items:center;margin-top:6px;color:var(--mute);font:12px var(--mono)}.tb{cursor:pointer;border:1px solid var(--line);background:var(--card);color:var(--dim);padding:8px 14px;border-radius:999px;font:600 13px var(--sans)}.tb.on{background:var(--ink);color:#000;border-color:var(--ink)}</style>
<script type="module">
const data=await (await fetch('data/catalog.json')).json();
const $=s=>document.querySelector(s);let tier='';const T=['proven','likely','maybe','no'];
const names={proven:'Proven on 20K',likely:'Likely fits',maybe:'Research',no:'Will not fit'};
$('#tiers').innerHTML=['',...T].map(t=>`<button class="tb ${t===tier?'on':''}" data-t="${t}">${t?names[t]:'All'} <span class="mono">${t?data.filter(c=>c.tier===t).length:data.length}</span></button>`).join('');
function esc(s){return String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]))}
function draw(){const q=$('#q').value.toLowerCase(),cat=$('#cat').value;
const rows=data.filter(c=>(!tier||c.tier===tier)&&(!cat||c.category===cat)&&(c.name+' '+c.systems).toLowerCase().includes(q));
$('#count').textContent=rows.length+' cores';
$('#grid').innerHTML=rows.map(c=>`<a class="core" href="${esc(c.repo)}" target="_blank" rel="noopener"><div style="display:flex;justify-content:space-between;gap:8px"><b>${esc(c.name)}</b><span class="pill ${c.tier}">${c.tier}</span></div><small>${esc(c.systems)}</small><small style="color:var(--mute);flex:0">${esc(c.note||'')}</small><div class="m"><span>${c.category}</span><span>${c.sdram?'SDRAM':'BRAM only'}</span></div>${c.mistang?`<object><a href="${esc(c.mistang)}" target="_blank" rel="noopener" style="color:var(--tang2);font:600 12px var(--mono)">MiSTang repo →</a></object>`:''}</a>`).join('');
for(const b of document.querySelectorAll('.tb'))b.classList.toggle('on',b.dataset.t===tier)}
$('#tiers').onclick=e=>{const b=e.target.closest('.tb');if(b){tier=b.dataset.t;draw()}};$('#q').oninput=draw;$('#cat').onchange=draw;draw();
</script>''')

page('how.html', 'MiSTang — how cores load from SD, and from the web', 'how.html', '''
<section style="padding-top:48px"><div class="wrap prose"><div class="eyebrow">Research notes · 2026-11-01</div><h2>Can a Tang Nano 20K load cores from an SD card?</h2>
<p class="sub">Short answer: <b>yes, indirectly</b>. A real MiSTer swaps the whole FPGA configuration from a Linux HPS. The Nano 20K has no HPS, but it has a Gowin multiboot path and a SPI flash big enough to stage a core. Everything below is marked with how sure we are.</p>

<h3>What is verified on the real board</h3>
<div class="callout ok">Measured on a Tang Nano 20K (FT2232 serial 2023030621) from node via the same <code>jtag.mjs</code>/<code>gowin.mjs</code> the browser uses.<br>
<b>IDCODE</b> 0x0000081B = GW2A(R)-18(C) · <b>Flash</b> Winbond W25Q64 (EF 40 17, 8 MiB) · <b>Flash read</b> 64 KiB in 0.42 s · <b>SRAM load</b> of a 907 418-byte bitstream in 4.8 s at 6 MHz TCK, status <code>0x6020</code> = DONE.</div>

<h3>The loading chain</h3>
<table><tr><th>Step</th><th>Mechanism</th><th>Status</th></tr>
<tr><td>1. Launcher boots</td><td>Bitstream at flash 0x000000, menu CPU (RISC-V) firmware at 0x100000 — same layout as Open Pocket GBC.</td><td><span class="pill proven">proven</span></td></tr>
<tr><td>2. Read core from SD</td><td>FatFs on the soft CPU reads <code>/MiSTang/cores/&lt;name&gt;.bin</code>.</td><td><span class="pill proven">proven</span> (SD + FatFs already in Open Pocket GBC)</td></tr>
<tr><td>3. Stage in flash</td><td>CPU erases 4 KiB sectors and programs 256 B pages into slot A (0x400000). ≈ 225 sectors for a 0.9 MB bitstream.</td><td><span class="pill proven">proven</span> (<code>flash.c</code> already does saves)</td></tr>
<tr><td>4. Reconfigure</td><td>Fabric pulls <code>RECONFIG_N</code> low; the FPGA reloads from the address in the <b>bitstream header</b> (key 0x52, 4 KiB granularity, UG290/UG702). Header is patchable: <code>patchMultiboot()</code> in Studio.</td><td><span class="pill maybe">to verify</span> — pad accessibility on the Nano 20K, needs a build with the pin enabled</td></tr>
<tr><td>5. Back to menu</td><td>Slot A's header points to 0x000000; cores pull RECONFIG_N on a button combo.</td><td><span class="pill maybe">to verify</span></td></tr></table>

<h3>Why not simply …</h3>
<ul><li><b>Partial reconfiguration:</b> GW2A has no ICAP-style primitive reachable from fabric.</li>
<li><b>Fabric drives its own JTAG / slave-SSPI:</b> JTAG pins are dedicated and wired to the FT2232; mode pins are fixed for MSPI.</li>
<li><b>One giant bitstream with all cores:</b> 20 736 LUT4 — a single NES already takes a large part of it.</li></ul>
<div class="callout">No-fabric alternative that works <b>today</b>: Studio writes the core into the flash slot over JTAG (measured above) and tells the FPGA to reload. SD staging is the standalone version of the same thing.</div>

<h3>Uploading a bitstream from github.io</h3>
<p>Yes — and it is implemented. Chrome and Edge expose <a href="https://developer.mozilla.org/en-US/docs/Web/API/WebUSB_API">WebUSB</a> on HTTPS pages, and github.io is HTTPS. The Tang Nano 20K’s on-board debugger is an FT2232 (0403:6010); channel A is JTAG. Studio speaks the FTDI MPSSE protocol directly over WebUSB, then the Gowin JTAG commands (ported from openFPGALoader): erase SRAM → <code>XFER_WRITE</code> → done, or JTAG-to-SPI bridge (IR 0x16) for the external flash.</p>
<table><tr><th>OS</th><th>Notes</th></tr>
<tr><td>macOS / Linux</td><td>Works with no driver. On Linux add a udev rule for 0403:6010.</td></tr>
<tr><td>Windows</td><td>Channel A must use WinUSB — install it once with Zadig (interface 0 only; leave interface 1, the serial port, alone).</td></tr>
<tr><td>Firefox / Safari</td><td>No WebUSB. Use Chrome, Edge or the desktop build.</td></tr>
<tr><td>Sipeed FT2232 firmware</td><td>Does not implement MPSSE 0x8E/0x8F; the driver uses TMS-only idle clocks.</td></tr></table>

<h3>Which cores can realistically come</h3>
<p>Budget: 20 736 LUT4, 828 Kbit BSRAM, 8 MB SDRAM. Proven ports exist for NES, SNES (ROM ≤ 3.75 MB), Game Boy/Color, WonderSwan, MSX2+. 8-bit consoles and computers and small arcade boards are the next wave. Genesis, PC Engine, GBA need trimming and are research items. PSX, N64, Saturn, Mega-CD, 32X, Neo Geo, ao486 and the <a href="https://github.com/owenb321/MiSTer_DVD">DVD player</a> need far more logic or memory bandwidth and will not fit. See the <a href="cores.html">catalog</a>.</p>

<h3>Flash map</h3>
<pre>0x000000  Launcher bitstream   (multiboot -> 0x400000)
0x100000  Launcher firmware    (u32 length + RV32E code)
0x200000  Core registry, settings, per-core config
0x400000  CORE SLOT A          (multiboot -> 0x000000)  &lt;= 1 MiB
0x500000  CORE SLOT B/C        pinned cores, copy-free A/B swap planned
0x7FF000  System settings</pre>
</div></section>''')
