#!/usr/bin/env python3
"""Generates docs/index.html, cores.html, how.html in the Open Pocket visual language."""
import json, pathlib
D = pathlib.Path(__file__).resolve().parent.parent / 'docs'
N = len(json.loads((D/'data/catalog.json').read_text()))
FONTS = '<link rel="preconnect" href="https://fonts.googleapis.com"><link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500&family=VT323&display=swap" rel="stylesheet">'
def nav(active, base=''):
    items = [('cores', 'Cores', 'cores.html'), ('how', 'How it works', 'how.html'), ('studio', 'Studio', 'studio/')]
    a = ''.join(f'<a class="{"on" if k == active else ""}" href="{base}{h}">{t}</a>' for k, t, h in items)
    return f'<nav class="top"><a class="brand" href="{base}index.html">MiSTang</a><div class="links">{a}</div><a class="gh" href="https://github.com/MiSTang-FPGA/MiSTang">GitHub</a></nav>'
FOOT = '<footer><div class="wrap"><span>MiSTang · multi-core FPGA platform for the Sipeed Tang Nano 20K</span><span>Cores are our own or from LakoMoor’s Open Pocket projects. <a href="https://github.com/MiSTang-FPGA">GitHub</a></span></div></footer>'
def page(name, title, active, body):
    (D/name).write_text(f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title}</title><meta name="description" content="MiSTang: many FPGA cores on one Tang Nano 20K. Web flasher, HDMI capture, core catalog."><link rel="stylesheet" href="assets/site.css">{FONTS}</head><body>{nav(active)}{body}{FOOT}</body></html>')

page('index.html', 'MiSTang', '', f'''
<section class="hero"><div class="wrap">
<div class="lcd">MULTI-CORE</div>
<h1>MiSTang.<br>Many cores on<br>one $25 FPGA.</h1>
<p class="lead">A launcher for the Sipeed Tang Nano 20K. Pick a core from an SD card, play, return to the menu. Flash and capture from your browser, with no vendor tools.</p>
<div class="btns"><a class="btn solid" href="studio/">Open Studio</a><a class="btn" href="how.html">How it works</a></div>
<div style="max-width:760px;margin:80px auto 0;text-align:left"><pre><span style="color:#7a7a7a">$ node tools/hw/idcode.mjs          # same code the browser runs</span>
JTAG IDCODE      0x0000081B  GW2A(R)-18(C)
SPI flash        Winbond W25Q64  EF 40 17  (8 MiB)
SRAM load        907 418 bytes in 4.8 s   status 0x6020  DONE
RECONFIG_N       fabric pulls pin 9 low  → FPGA reloads at header address
                 USERCODE 0x4EAC → 0xFD4B</pre><p class="caption">Measured on a real Tang Nano 20K, 2026-11-01.</p></div>
</div></section>

<section class="light"><div class="wrap">
<p class="eyebrow">Cores from SD</p><h2>One slot.<br>Any core.</h2>
<p class="lead">The FPGA cannot read an SD card into its own configuration, so the launcher stages the chosen core in a flash slot and asks the FPGA to reload from it.</p>
<div class="grid4">
<div class="feat"><h3>1 · Read</h3><p>The menu CPU reads <code>/MiSTang/cores/&lt;id&gt;.bin</code> from the card.</p></div>
<div class="feat"><h3>2 · Stage</h3><p>It writes the bitstream and the core’s firmware into slot A of the SPI flash.</p></div>
<div class="feat"><h3>3 · Reload</h3><p>The fabric pulls <code>RECONFIG_N</code> low. The FPGA boots the multiboot address from the bitstream header.</p></div>
<div class="feat"><h3>4 · Return</h3><p>Holding S1 + S2 pulls the pin again. Slot A points back to the launcher.</p></div>
</div></div></section>

<section><div class="wrap split">
<div><p class="eyebrow">Web Studio</p><h2>Flash from<br>github.io.</h2>
<p class="lead">WebUSB speaks MPSSE to the board’s FT2232, then Gowin JTAG: load into SRAM, write the SPI flash, verify. Chrome or Edge, no drivers on macOS and Linux.</p>
<div class="btns" style="justify-content:flex-start;margin-top:30px"><a class="btn solid" href="studio/">Open Studio</a></div></div>
<div><div class="feat"><h3>Load</h3><p>Drop a Gowin <code>.fs</code> or <code>.bin</code>. Run it from SRAM in five seconds or write it to a flash slot with verification.</p></div>
<div class="feat" style="margin-top:22px"><h3>Capture</h3><p>Any UVC capture card on the HDMI output: live view, pixel-perfect scaling, PNG screenshots, WebM recording with audio.</p></div>
<div class="feat" style="margin-top:22px"><h3>SD card</h3><p>Prepare the folder layout and convert bitstreams so every core can find its way back.</p></div></div>
</div></section>

<section class="light"><div class="wrap">
<p class="eyebrow">Cores</p><h2>Our own<br>cores.</h2>
<p class="lead">Cores are written here or come from the Open Pocket projects. The catalog maps the {N} systems of the MiSTer core list to what fits into 20 736 LUT4.</p>
<div class="grid3">
<div class="feat"><div class="big-num">2</div><h3>Core repositories</h3><p><a href="https://github.com/MiSTang-FPGA/mistang-core-gbc">Game Boy / Color</a> and <a href="https://github.com/MiSTang-FPGA/mistang-core-ws">WonderSwan / Color</a>, both from Open Pocket.</p></div>
<div class="feat"><div class="big-num">{N}</div><h3>Systems in the catalog</h3><p>Console, computer, arcade and other. Sorted by whether they fit, not by hype.</p></div>
<div class="feat"><div class="big-num">20 736</div><h3>LUT4 to share</h3><p>Plus 828 Kbit of block RAM and 8 MB of SDRAM. PSX, N64 and Saturn will not fit.</p></div>
</div>
<div class="btns" style="justify-content:flex-start;margin-top:50px"><a class="btn" href="cores.html">Browse the catalog</a></div>
</div></section>

<section><div class="wrap"><p class="eyebrow">Read more</p><h2>Details.</h2>
<div class="doclinks"><a href="how.html">How cores load from SD<span>→</span></a><a href="cores.html">Core catalog<span>→</span></a><a href="studio/">Web Studio<span>→</span></a>
<a href="https://github.com/MiSTang-FPGA/MiSTang/blob/main/docs/design/launcher.md">Launcher design<span>→</span></a><a href="https://github.com/MiSTang-FPGA/MiSTang/tree/main/hwtest/reconfig">RECONFIG_N test<span>→</span></a><a href="https://github.com/MiSTang-FPGA">GitHub organisation<span>→</span></a></div></div></section>''')

page('cores.html', 'MiSTang · Catalog', 'cores.html', '''
<section class="page"><div class="wrap"><p class="eyebrow">Catalog</p><h1>What fits in 20 736 LUT4.</h1>
<p class="lead">The systems of the MiSTer core lists, sorted by an honest guess. “Proven” means a port already runs on a Tang Nano 20K. Links lead to the original projects as reference; MiSTang cores are our own.</p>
<div id="tiers" style="display:flex;gap:8px;flex-wrap:wrap;margin:40px 0 14px"></div>
<div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:22px"><input id="q" placeholder="Search — nes, pac-man, amstrad…" style="flex:1;min-width:240px"><select id="cat"><option value="">All types</option><option>console</option><option>computer</option><option>arcade</option><option>other</option></select></div>
<div id="count" class="caption" style="margin-bottom:10px"></div><div id="grid"></div></div></section>
<style>input,select{background:#0d0d0d;color:#fff;border:1px solid #3c3c3c;border-radius:100px;padding:12px 18px;font:15px var(--sans)}
.tb{cursor:pointer;border:1px solid #3c3c3c;background:transparent;color:#a6a6a6;padding:8px 16px;border-radius:100px;font:14px var(--sans)}.tb.on{background:#fff;color:#000;border-color:#fff}
.row{display:grid;grid-template-columns:minmax(150px,1.2fr) 3fr auto auto;gap:18px;padding:15px 0;border-bottom:1px solid var(--hair);align-items:baseline;text-decoration:none}.row:hover b{text-decoration:underline}
.row b{font-weight:500;font-size:17px}.row small{color:#7a7a7a;font-size:14px}.row .k{color:#7a7a7a;font-size:13px;white-space:nowrap}
@media(max-width:760px){.row{grid-template-columns:1fr auto}.row small,.row .k{display:none}}</style>
<script type="module">
const data=await (await fetch('data/catalog.json')).json();const $=s=>document.querySelector(s);let tier='';const T=['proven','likely','maybe','no'];
const names={proven:'Proven on 20K',likely:'Likely',maybe:'Research',no:'Will not fit'};
$('#tiers').innerHTML=['',...T].map(t=>`<button class="tb" data-t="${t}">${t?names[t]:'All'} ${t?data.filter(c=>c.tier===t).length:data.length}</button>`).join('');
const esc=s=>String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
function draw(){const q=$('#q').value.toLowerCase(),cat=$('#cat').value;const rows=data.filter(c=>(!tier||c.tier===tier)&&(!cat||c.category===cat)&&(c.name+' '+c.systems).toLowerCase().includes(q));
$('#count').textContent=rows.length+' systems';
$('#grid').innerHTML=rows.map(c=>`<a class="row" href="${esc(c.mistang||c.repo)}" target="_blank" rel="noopener"><b>${esc(c.name)}</b><small>${esc(c.systems)}</small><span class="k">${c.category}${c.sdram?' · SDRAM':''}</span><span class="pill ${c.tier}">${c.mistang?'MiSTang repo':c.tier}</span></a>`).join('');
for(const b of document.querySelectorAll('.tb'))b.classList.toggle('on',b.dataset.t===tier)}
$('#tiers').onclick=e=>{const b=e.target.closest('.tb');if(b){tier=b.dataset.t;draw()}};$('#q').oninput=draw;$('#cat').onchange=draw;draw();
</script>''')

page('how.html', 'MiSTang · How it works', 'how.html', '''
<section class="page"><div class="wrap prose"><p class="eyebrow">Research notes · 2026-11-01</p><h1>Cores from an SD card.</h1>
<p class="lead">A MiSTer swaps the whole FPGA configuration from a Linux HPS. The Nano 20K has none, but it has a Gowin multiboot path and a SPI flash large enough to stage a core.</p>

<h3>Measured on the board</h3>
<div class="callout">Tang Nano 20K, FT2232 serial 2023030621, driven with the same <code>jtag.mjs</code> and <code>gowin.mjs</code> the browser uses.<br>
IDCODE <code>0x0000081B</code> (GW2A(R)-18) · SPI flash Winbond W25Q64, 8 MiB · 64 KiB read in 0.42 s · SRAM load of 907 418 bytes in 4.8 s (openFPGALoader takes the same 4.75 s) · flash erase, write, verify and erase again on a 4 KiB sector.</div>
<div class="callout"><b>RECONFIG_N works from the fabric.</b> Design A, packed with <code>--multiboot_address 0x4F0000</code>, was loaded into SRAM and pulled pin 9 (IOR31B) low after about five seconds. Design B sat in flash at 0x4F0000. Seven to eight seconds after loading, the USERCODE read over JTAG changed from <code>0x4EAC</code> to <code>0xFD4B</code>, which is B’s value when loaded directly. No wire was added. The test region was blank and was erased afterwards. Source: <a href="https://github.com/MiSTang-FPGA/MiSTang/tree/main/hwtest/reconfig">hwtest/reconfig</a>.</div>

<h3>The loading chain</h3>
<table><tr><th>Step</th><th>Mechanism</th><th>State</th></tr>
<tr><td>Launcher boots</td><td>Bitstream at flash 0x000000, menu CPU firmware in flash.</td><td>design</td></tr>
<tr><td>Read core from SD</td><td>FatFs on the soft CPU, already used by Open Pocket GBC.</td><td>exists</td></tr>
<tr><td>Stage in flash</td><td>Erase 4 KiB sectors, program 256 B pages into slot A at 0x400000; bitstream first, core firmware at +1 MiB.</td><td>exists (flash.c)</td></tr>
<tr><td>Reload</td><td>Fabric pulls RECONFIG_N low; the FPGA loads the address in the header of the running bitstream.</td><td><b>measured</b></td></tr>
<tr><td>Back to the menu</td><td>The core’s header points to 0x000000; S1 + S2 held for 1.5 s pull the pin.</td><td>built into GBC and WS, button test pending</td></tr></table>

<h3>Why not something simpler</h3>
<ul><li>Partial reconfiguration: GW2A has no ICAP-style primitive reachable from the fabric.</li>
<li>Fabric driving its own JTAG or slave SSPI: the JTAG pins are dedicated and wired to the FT2232.</li>
<li>One bitstream with every core: a single core already fills most of the 20 736 LUT4.</li></ul>

<h3>Uploading a bitstream from github.io</h3>
<p>Chrome and Edge expose <a href="https://developer.mozilla.org/en-US/docs/Web/API/WebUSB_API">WebUSB</a> on HTTPS pages. The board’s debugger is an FT2232 (0403:6010) and channel A is JTAG. Studio speaks FTDI MPSSE directly, then the Gowin sequence: erase SRAM, <code>XFER_WRITE</code>, done; or the JTAG-to-SPI bridge (IR 0x16) for the external flash.</p>
<table><tr><th>Platform</th><th>Notes</th></tr>
<tr><td>macOS, Linux</td><td>Works without a driver. Linux needs a udev rule for 0403:6010.</td></tr>
<tr><td>Windows</td><td>Interface 0 needs WinUSB (Zadig). Leave interface 1, the serial port, alone.</td></tr>
<tr><td>Firefox, Safari</td><td>No WebUSB.</td></tr>
<tr><td>Sipeed firmware</td><td>No MPSSE commands 0x8E and 0x8F, so idle clocks use TMS-only shifts.</td></tr></table>

<h3>Flash map</h3>
<pre>0x000000  Launcher bitstream      multiboot → 0x400000
0x100000  Launcher firmware
0x200000  Registry, settings
0x400000  Core slot A: bitstream (≤ 1 MiB)   multiboot → 0x000000
0x500000  Core slot A: core firmware (≤ 1 MiB)
0x7FF000  System settings</pre>
<p class="caption">A board that ran Open Pocket GBC holds ROMs and saves across most of this range. Dump the flash before writing.</p>
</div></section>''')
