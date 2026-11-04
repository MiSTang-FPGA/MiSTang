#!/usr/bin/env python3
"""Generates docs/index.html, cores.html, how.html in the Open Pocket visual language."""
import json, pathlib
D = pathlib.Path(__file__).resolve().parent.parent / 'docs'
N = len(json.loads((D/'data/catalog.json').read_text()))
FONTS = '<link rel="preconnect" href="https://fonts.googleapis.com"><link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500&family=VT323&display=swap" rel="stylesheet">'
def nav(active, base=''):
    items = [('ours', 'Our cores', 'ours.html'), ('cores', 'Catalog', 'cores.html'), ('how', 'How it works', 'how.html'), ('roadmap', 'Roadmap', 'roadmap.html'), ('studio', 'Studio', 'studio/')]
    a = ''.join(f'<a class="{"on" if k == active else ""}" href="{base}{h}">{t}</a>' for k, t, h in items)
    return f'<nav class="top"><a class="brand" href="{base}index.html">MiSTang</a><div class="links">{a}</div><a class="gh" href="https://github.com/MiSTang-FPGA/MiSTang">GitHub</a></nav>'
FOOT = '<footer><div class="wrap"><span>MiSTang · multi-core FPGA platform for the Sipeed Tang Nano 20K</span><span>Cores are our own or from LakoMoor’s Open Pocket projects. <a href="https://github.com/MiSTang-FPGA">GitHub</a></span></div></footer>'
def page(name, title, active, body, head=''):
    (D/name).write_text(f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title}</title><meta name="description" content="MiSTang: many FPGA cores on one Tang Nano 20K. Web flasher, HDMI capture, core catalog."><link rel="stylesheet" href="assets/site.css">{head}{FONTS}</head><body>{nav(active)}{body}{FOOT}</body></html>')

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

<section id="stage"><div class="wrap"><p class="eyebrow">Inside</p><h2>One board.<br>Every piece, shown.</h2>
<p class="lead">The launcher menu below is drawn from the firmware’s layout. The frames are real captures from the board.</p>
<div class="bento" id="bento">
<div class="tile span2 lead-tile" style="--i:0"><h3>Pick a core. <span>The launcher lists what is on your SD card.</span></h3>
<div class="pic"><div class="win"><div class="bar"><i></i><i></i><i></i><b>MiSTang launcher</b></div>
<div class="osd"><div class="pill"><span>MiSTang</span><em>choose a core</em></div>
<ul><li><span>Apple I</span><small>886 KB</small></li><li><span><span class="dot">*</span>Breakout</span><small>563 KB</small></li><li class="sel"><span>CHIP-8</span><small>886 KB</small></li><li><span>Pong</span><small>563 KB</small></li></ul>
<div class="hint">A: start&nbsp;&nbsp; Y: rescan&nbsp;&nbsp; * = in flash<span class="cur"></span></div></div></div></div>
<span class="tag">Illustration, not a photo</span></div>

<div class="tile stat" style="--i:1"><div><p class="lead">Loads in</p><p class="num">4.8<u>s</u></p><p class="s">A 907 KB bitstream into the FPGA from your browser. Measured on the board.</p></div>
<div class="ticks"><i style="--k:0"></i><i style="--k:1"></i><i style="--k:2"></i><i style="--k:3"></i><i style="--k:4"></i><i style="--k:5"></i></div></div>

<div class="tile" style="--i:2"><h3>Real frames.</h3>
<div class="pic"><div class="shots"><img src="img/core-pong-board.png" alt="Pong captured from the board"><img src="img/core-apple1-board.png" alt="Apple I captured from the board"><img src="img/core-breakout-hdmi.png" alt="Breakout captured from the board"></div></div></div>

<div class="tile" style="--i:3"><h3>Write and verify. <span>From the browser.</span></h3>
<div class="pic"><div class="flash"><div class="row"><div class="ic">.fs</div><div class="nm"><b>launcher.fs</b><span>907 418 bytes · slot 0x000000</span></div></div>
<div class="bar"><i></i></div><div class="meta"><span>Erase · write · read back</span><span>31 s</span></div><div class="ok">Verified</div><div class="ghost"></div></div></div></div>

<div class="tile" style="--i:4"><h3>One slot. <span>Any core.</span></h3>
<div class="pic"><div class="map"><div class="seg"><i class="a"></i><i class="b"></i><i class="c"></i><i class="d"></i><i class="e"></i></div>
<div class="lab"><span class="a">Launcher</span><span class="d">Core slot A</span><span class="e">8 MiB flash</span></div>
<div class="jump"><svg viewBox="0 0 300 34" preserveAspectRatio="none"><path d="M150 2 C150 30 40 30 18 7"/><path class="hd" d="M12 4 L22 4 L18 12 Z" style="stroke:none"/></svg></div></div></div></div>

<div class="tile span3 state" style="--i:5"><p class="big">574 systems mapped. <span>Six cores of our own.</span></p>
<div class="side"><p>Sorted by whether they fit into 20 736 LUT4, not by hype.</p><div class="btns" style="justify-content:flex-start"><a class="btn solid" href="cores.html">Browse the catalog</a><a class="btn" href="ours.html">Our cores</a></div></div></div>
</div></div></section>
<script>(function(){{var b=document.getElementById('bento');if(!b)return;if(!('IntersectionObserver'in window)){{b.classList.add('in');return}}
var o=new IntersectionObserver(function(e){{if(e[0].isIntersecting){{b.classList.add('in');o.disconnect()}}}},{{threshold:.15}});o.observe(b)}})()</script>

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
<p class="lead">Cores are written here or come from the Open Pocket projects. The catalog lists {N} systems from the MiSTer core lists and our own project list, and marks what fits into 20 736 LUT4.</p>
<div class="grid3">
<div class="feat"><div class="big-num">5</div><h3>Core repositories</h3><p><a href="https://github.com/MiSTang-FPGA/mistang-core-gbc">Game Boy / Color</a> and <a href="https://github.com/MiSTang-FPGA/mistang-core-ws">WonderSwan / Color</a> from Open Pocket, plus <a href="https://github.com/MiSTang-FPGA/mistang-core-chip8">CHIP-8</a>, <a href="https://github.com/MiSTang-FPGA/mistang-core-pong">Pong</a> and <a href="https://github.com/MiSTang-FPGA/mistang-core-apple1">Apple I</a> written from scratch. <a href="ours.html">Status of each</a>.</p></div>
<div class="feat"><div class="big-num">{N}</div><h3>Systems in the catalog</h3><p>Console, computer, arcade and other. Sorted by whether they fit, not by hype.</p></div>
<div class="feat"><div class="big-num">20 736</div><h3>LUT4 to share</h3><p>Plus 828 Kbit of block RAM and 8 MB of SDRAM. PSX, N64 and Saturn will not fit.</p></div>
</div>
<div class="btns" style="justify-content:flex-start;margin-top:50px"><a class="btn" href="cores.html">Browse the catalog</a></div>
</div></section>

<section><div class="wrap"><p class="eyebrow">Read more</p><h2>Details.</h2>
<div class="doclinks"><a href="how.html">How cores load from SD<span>→</span></a><a href="cores.html">Core catalog<span>→</span></a><a href="studio/">Web Studio<span>→</span></a>
<a href="https://github.com/MiSTang-FPGA/MiSTang/blob/main/docs/design/launcher.md">Launcher design<span>→</span></a><a href="https://github.com/MiSTang-FPGA/MiSTang/tree/main/hwtest/reconfig">RECONFIG_N test<span>→</span></a><a href="https://github.com/MiSTang-FPGA">GitHub organisation<span>→</span></a></div></div></section>''', head='<link rel="stylesheet" href="assets/stage.css">')

page('ours.html', 'MiSTang · Our cores', 'ours', '''
<section class="page"><div class="wrap"><p class="eyebrow">Our cores</p><h1>What we have built.</h1>
<p class="lead">Every core here is our own: written from scratch or taken from LakoMoor’s Open Pocket projects. Each one lives in its own repository and is checked before it is listed. “Simulation” means verified against a reference model, “Board” means it runs on a Tang Nano 20K.</p>
<div id="ours" style="margin-top:50px"></div></div></section>
<style>.oc{display:grid;grid-template-columns:minmax(240px,1fr) 2fr;gap:34px;padding:34px 0;border-top:1px solid var(--hair)}
.oc img{width:100%;image-rendering:pixelated;border:1px solid #3c3c3c;background:#0b0b0b}.oc .noimg{display:flex;align-items:center;justify-content:center;aspect-ratio:4/3;border:1px dashed #3c3c3c;color:#7a7a7a;font-size:14px}
.oc h3{margin:0 0 6px;font-weight:500;font-size:24px}.oc .sys{color:#7a7a7a;margin-bottom:14px}.oc p{color:#bdbdbd;line-height:1.55}.oc a{color:#fff}
.st{display:inline-block;margin-right:10px;padding:4px 12px;border:1px solid #3c3c3c;border-radius:100px;font-size:13px;color:#a6a6a6}.st.board{background:#fff;color:#000;border-color:#fff}
@media(max-width:760px){.oc{grid-template-columns:1fr}}</style>
<script type="module">
const data=await (await fetch('data/ours.json')).json();
const esc=s=>String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const label={board:'Board',sim:'Simulation',wip:'In progress'};
document.querySelector('#ours').innerHTML=data.map(c=>`<div class="oc"><div>${c.image?`<img src="${esc(c.image)}" alt="${esc(c.name)}"><div class="caption" style="margin-top:8px">${esc(c.image_note)}</div>`:'<div class="noimg">no screenshot yet</div>'}</div>
<div><h3>${esc(c.name)}</h3><div class="sys">${esc(c.system)} · ${esc(c.origin)}</div><span class="st ${c.state}">${label[c.state]||c.state}</span>
<p>${esc(c.verified)}</p>${c.repo?`<p><a href="https://github.com/MiSTang-FPGA/${esc(c.repo)}">github.com/MiSTang-FPGA/${esc(c.repo)}</a></p>`:''}</div></div>`).join('');
</script>''')

page('cores.html', 'MiSTang · Catalog', 'cores', '''
<section class="page"><div class="wrap"><p class="eyebrow">Catalog</p><h1>What fits in 20 736 LUT4.</h1>
<p class="lead">The MiSTer core lists plus our own project list, sorted by an honest guess. “Not assessed” entries have a search link, not a repository. “Proven” means a port already runs on a Tang Nano 20K. Links lead to the original projects as reference; MiSTang cores are our own.</p>
<div id="tiers" style="display:flex;gap:8px;flex-wrap:wrap;margin:40px 0 14px"></div>
<div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:22px"><input id="q" placeholder="Search — nes, pac-man, amstrad…" style="flex:1;min-width:240px"><select id="cat"><option value="">All types</option><option>console</option><option>computer</option><option>arcade</option><option>other</option></select></div>
<div id="count" class="caption" style="margin-bottom:10px"></div><div id="grid"></div></div></section>
<style>input,select{background:#0d0d0d;color:#fff;border:1px solid #3c3c3c;border-radius:100px;padding:12px 18px;font:15px var(--sans)}
.tb{cursor:pointer;border:1px solid #3c3c3c;background:transparent;color:#a6a6a6;padding:8px 16px;border-radius:100px;font:14px var(--sans)}.tb.on{background:#fff;color:#000;border-color:#fff}
.row{display:grid;grid-template-columns:minmax(150px,1.2fr) 3fr auto auto;gap:18px;padding:15px 0;border-bottom:1px solid var(--hair);align-items:baseline;text-decoration:none}.row:hover b{text-decoration:underline}
.row b{font-weight:500;font-size:17px}.row small{color:#7a7a7a;font-size:14px}.row .k{color:#7a7a7a;font-size:13px;white-space:nowrap}
@media(max-width:760px){.row{grid-template-columns:1fr auto}.row small,.row .k{display:none}}</style>
<script type="module">
const data=await (await fetch('data/catalog.json')).json();const $=s=>document.querySelector(s);let tier='';const T=['proven','likely','maybe','idea','no'];
const names={proven:'Proven on 20K',likely:'Likely',maybe:'Research',idea:'Not assessed',no:'Will not fit'};
$('#tiers').innerHTML=['',...T].map(t=>`<button class="tb" data-t="${t}">${t?names[t]:'All'} ${t?data.filter(c=>c.tier===t).length:data.length}</button>`).join('');
const esc=s=>String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
function draw(){const q=$('#q').value.toLowerCase(),cat=$('#cat').value;const rows=data.filter(c=>(!tier||c.tier===tier)&&(!cat||c.category===cat)&&(c.name+' '+c.systems).toLowerCase().includes(q));
$('#count').textContent=rows.length+' systems';
$('#grid').innerHTML=rows.map(c=>`<a class="row" href="${esc(c.mistang||c.repo)}" target="_blank" rel="noopener"><b>${esc(c.name)}</b><small>${esc(c.systems)}</small><span class="k">${c.category}${c.sdram?' · SDRAM':''}</span><span class="pill ${c.tier}">${c.mistang?'MiSTang repo':c.tier}</span></a>`).join('');
for(const b of document.querySelectorAll('.tb'))b.classList.toggle('on',b.dataset.t===tier)}
$('#tiers').onclick=e=>{const b=e.target.closest('.tb');if(b){tier=b.dataset.t;draw()}};$('#q').oninput=draw;$('#cat').onchange=draw;draw();
</script>''')

page('how.html', 'MiSTang · How it works', 'how', '''
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

page('roadmap.html', 'MiSTang · Roadmap', 'roadmap', '''
<section class="hero" style="min-height:auto;padding-bottom:40px"><div class="wrap"><div class="lcd">ROADMAP</div><h1>What works.<br>What is next.</h1>
<p class="lead">Ordered by priority. Status is what has actually been run, not what is planned.</p></div></section>
<section class="light"><div class="wrap"><table>
<tr><th>#</th><th>Item</th><th>Status</th></tr>
<tr><td>1</td><td>Web flasher: JTAG, SRAM load, SPI flash write and verify</td><td>Working, tested on a board</td></tr>
<tr><td>2</td><td>Launcher: SD card → flash slot → RECONFIG_N switch (<a href="https://github.com/MiSTang-FPGA/MiSTang/tree/main/launcher">launcher/</a>)</td><td>Firmware written, syntax-checked only. Not built or run yet</td></tr>
<tr><td>3</td><td>Studio capture, serial remote, SD preparation</td><td>Written, not yet exercised on hardware</td></tr>
<tr><td>4</td><td>Ports of small GPL MiSTer cores (<code>tools/portcore.py</code> scaffolds them): SMS, ColecoVision, VIC-20 and similar</td><td>Tooling only, no port built</td></tr>
<tr><td>5</td><td>RISC-V soft cores (<a href="https://github.com/MiSTang-FPGA/MiSTang/blob/main/docs/design/riscv.md">notes</a>), then uClinux nommu with busybox</td><td>Desk study</td></tr>
<tr><td>6</td><td>XNU / Darwin, zsh, fastfetch</td><td>Last. No RISC-V port of XNU exists and the board has 8 MB of RAM; see the notes above</td></tr>
</table></div></section>''')
