#!/usr/bin/env python3
"""Start a MiSTang port of a MiSTer core: clone it, audit what the MiSTer `sys/` framework provides to it,
and write a scaffold (<out>/mistang-core-<id>/) with PORTING.md listing the glue that has to be replaced.

usage: portcore.py https://github.com/MiSTer-devel/SMS_MiSTer --id sms -o ports/
No synthesis happens here: the audit is a text scan and only tells you where the work is.
The MiSTer core stays GPL; keep its LICENSE and credit the authors (the scaffold copies both)."""
import argparse, pathlib, re, shutil, subprocess, sys, tempfile

HERE = pathlib.Path(__file__).resolve().parent
# what a MiSTer core pulls in from sys/ and what replaces it on the Tang Nano 20K (iosys + memsys from open-pocket-gbc)
GLUE = [
    (r'\bhps_io\b', 'hps_io', 'file loading, OSD status bits, joysticks: replace with iosys ioctl_* (SD loader) and the launcher menu'),
    (r'\bpll\b|\bpll_cfg\b', 'PLL', 'Cyclone PLL IP: replace with Gowin rPLL (rtl/board/pll_*.v), 27 MHz in'),
    (r'\bSDRAM_[A-Z]+\b|\bsdram\b', 'SDRAM', 'external SDRAM controller: Tang has 8 MB SDR in package (sdram_ctrl.sv, 32-bit words, 5 clocks/access)'),
    (r'\bDDRAM_[A-Z]+\b|\bddram\b', 'DDR3 (HPS)', 'DDR3 on the HPS side does not exist: move to SDRAM or BSRAM; usually the hard part'),
    (r'\bVGA_[A-Z]+\b|\bHDMI_[A-Z]+\b|\bvideo_mixer\b|\barcade_video\b', 'video out', 'scaler/mixer: feed pixels to fb_writer, video_out scales to 720x480'),
    (r'\bAUDIO_[LS]\b|\bAUDIO_MIX\b', 'audio', 'audio_out.sv (sigma-delta) and the HDMI audio packets'),
    (r'\baltsyncram\b|\baltera_[a-z_]+\b|\blpm_[a-z_]+\b', 'Altera megafunctions', 'rewrite as inferred RAM / Gowin BSRAM (gowin_prims.v)'),
    (r'\bdcfifo\b|\bscfifo\b', 'Altera FIFO', 'replace with a simple dual-clock FIFO'),
    (r'\bUART_[A-Z]+\b|\bUSER_[A-Z]+\b', 'user port', 'unused on Tang; tie off'),
    (r'\bSD_[A-Z]+\b', 'SD (core side)', 'handled by the launcher firmware, not the core'),
]
SIZE_HINT = [
    (r'\bT80\w*\b', 'Z80 (T80)'), (r'\bT65\b|\bP65C02\b|\bcpu6502\b', '6502'), (r'\bTG68\w*\b|\bfx68k\b', '68000'),
    (r'\bmc6809\w*\b', '6809'), (r'\bz8\w*\b', 'Z8'), (r'\bI8080\b|\bi8085\b', '8080/85'), (r'\bcpu_gb\b|\bgb\b', 'GB-like SoC'),
]

def sh(*a, **k): return subprocess.run(a, check=True, text=True, capture_output=True, **k).stdout

def audit(root):
    files = [p for p in root.rglob('*') if p.suffix.lower() in ('.v', '.sv', '.vhd', '.vhdl', '.qip', '.sdc', '.qsf') and '.git' not in p.parts]
    src = [p for p in files if p.suffix.lower() in ('.v', '.sv', '.vhd', '.vhdl') and 'sys' not in p.relative_to(root).parts[:1]]
    text = {p: p.read_text(errors='replace') for p in src}
    lines = sum(t.count('\n') for t in text.values())
    top = next((p for p in src if re.search(r'module\s+emu\b', text[p])), None)
    res = []
    for pat, name, note in GLUE:
        hits = sorted({str(p.relative_to(root)) for p, t in text.items() if re.search(pat, t)})
        if hits: res.append((name, note, hits))
    cpus = sorted({n for pat, n in SIZE_HINT for t in text.values() if re.search(pat, t)})
    conf = re.search(r'CONF_STR\s*=\s*\{(.*?)\};', text[top] if top else '', re.S)
    return dict(lines=lines, nfiles=len(src), top=top and str(top.relative_to(root)), glue=res, cpus=cpus,
                conf=(re.findall(r'"([^"]*)"', conf.group(1)) if conf else []))

def report(name, url, a):
    o = [f'# Porting {name} to the Tang Nano 20K\n', f'Source: {url}  (GPL, keep LICENSE and credit upstream authors)\n',
         f'- HDL files scanned: {a["nfiles"]} ({a["lines"]} lines, excluding `sys/`)',
         f'- Top module `emu`: `{a["top"] or "not found"}`', f'- CPU/IP hints: {", ".join(a["cpus"]) or "none detected"}\n',
         '## MiSTer framework dependencies to replace\n', '| Dependency | What to do | Used in |', '|---|---|---|']
    for n, note, hits in a['glue']:
        o.append(f'| {n} | {note} | {", ".join(hits[:3])}{" …" if len(hits) > 3 else ""} |')
    if a['conf']:
        o += ['\n## OSD menu (CONF_STR) to map onto the launcher menu / core config bits\n', '```'] + a['conf'] + ['```']
    o += ['\n## Checklist\n', '- [ ] Fits: synthesise with `synth_gowin`; budget 20 736 LUT4, 46 BSRAM(18 Kb) pairs, 8 MB SDRAM',
          '- [ ] Clocks: single rPLL, clock enables instead of derived clocks', '- [ ] Memory: ROM/RAM from SDRAM through `memsys`',
          '- [ ] Video into `fb_writer`, audio into `audio_out`', '- [ ] Loader: `ioctl_*` driven by launcher firmware (SD → SDRAM)',
          '- [ ] Return to launcher: `mistang_return` on SELECT+START',
          '- [ ] Simulation check against upstream behaviour before touching hardware', '- [ ] Package: `tools/mkcore.py`']
    return '\n'.join(o) + '\n'

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('repo'); ap.add_argument('--id', required=True); ap.add_argument('-o', default='ports')
    ap.add_argument('--template', default='https://github.com/MiSTang-FPGA/mistang-core-template')
    ap.add_argument('--local', help='use an already cloned MiSTer repo instead of cloning')
    a = ap.parse_args()
    out = pathlib.Path(a.o) / f'mistang-core-{a.id}'
    if out.exists(): sys.exit(f'{out} exists')
    with tempfile.TemporaryDirectory() as td:
        up = pathlib.Path(a.local) if a.local else pathlib.Path(td) / 'up'
        if not a.local: sh('git', 'clone', '--depth', '1', '-q', a.repo, str(up))
        sh('git', 'clone', '--depth', '1', '-q', a.template, str(out))
        shutil.rmtree(out / '.git', ignore_errors=True)
        res = audit(up)
        (out / 'upstream').mkdir()
        for lic in list(up.glob('LICENSE*')) + list(up.glob('COPYING*')): shutil.copy(lic, out / 'upstream' / lic.name)
        for sub in ('rtl',):
            if (up / sub).is_dir(): shutil.copytree(up / sub, out / 'upstream' / sub, ignore=shutil.ignore_patterns('.git'))
        for f in up.glob('*.sv'): shutil.copy(f, out / 'upstream' / f.name)
        for f in up.glob('*.v'): shutil.copy(f, out / 'upstream' / f.name)
        (out / 'PORTING.md').write_text(report(a.id.upper(), a.repo, res), encoding='utf-8')
    print(f'scaffold: {out}\n{len(res["glue"])} framework dependencies found, see {out}/PORTING.md')

if __name__ == '__main__': main()
