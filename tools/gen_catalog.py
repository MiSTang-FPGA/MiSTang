#!/usr/bin/env python3
"""Build cores/catalog.json from the MiSTer MkDocs core tables + hand-made feasibility notes.

Budget of the Tang Nano 20K (GW2AR-18): 20736 LUT4, 46 BSRAM (828 Kbit), 48 DSP-ish mult,
8 MB on-package SDR SDRAM (shared with framebuffer), 64 Mbit SPI flash, 2 PLL, HDMI + SD slot.
Tiers: proven (an open Tang Nano 20K port exists) / likely / maybe / no.
"""
import re, json, sys, pathlib
ref = pathlib.Path(sys.argv[1]); out = pathlib.Path(sys.argv[2])
row = re.compile(r'^\|\s*\[([^\]]+)\]\(([^)]+)\)[^|]*\|(.*)$')

def rows(fn, cat):
    for line in (ref/fn).read_text().splitlines():
        m = row.match(line)
        if not m: continue
        name, url, rest = m.groups()
        cells = [c.strip() for c in rest.split('|')][:-1] if rest.rstrip().endswith('|') else [c.strip() for c in rest.split('|')]
        url = url.split('{')[0]
        if url.startswith('./'): url = 'https://mister-devel.github.io/MkDocs_MiSTer/cores/' + url[2:]
        yield dict(name=name, repo=url, category=cat, cells=cells)

cores = []
for r in rows('console.md','console'):
    c = r.pop('cells'); r['systems'] = c[0].replace('<br>', ' / ') if c else ''
    r['sdram'] = any('✔' in x for x in c[-1:]) ; cores.append(r)
for r in rows('computer.md','computer'):
    c = r.pop('cells'); r['systems'] = c[0].replace('<br>', ' / ') if c else ''
    r['sdram'] = any('✔' in x for x in c[-1:]); cores.append(r)
for r in rows('other.md','other'):
    c = r.pop('cells'); r['systems'] = c[0] if c else ''; r['sdram']=False; cores.append(r)
for r in rows('arcade.md','arcade'):
    c = r.pop('cells'); r['systems'] = c[0].replace('<br>', ' / ') if c else ''
    r['sdram'] = any('✔' in x for x in c[-1:]); cores.append(r)

# extra non-MkDocs entries
cores += [
 dict(name='DVD', repo='https://github.com/owenb321/MiSTer_DVD', category='other', systems='DVD-Video player (menus, subtitles, AC-3 in fabric)', sdram=True),
 dict(name='NESTang', repo='https://github.com/nand2mario/nestang', category='console', systems='Nintendo NES / Famicom (Tang Nano 20K port)', sdram=True),
 dict(name='SNESTang', repo='https://github.com/nand2mario/snestang', category='console', systems='Nintendo SNES (Tang Nano 20K, ROM <= 3.75 MB)', sdram=True),
 dict(name='Open Pocket GBC', repo='https://github.com/LakoMoor/open-pocket-gbc', category='console', systems='Game Boy / Game Boy Color', sdram=True),
 dict(name='Open Pocket WS', repo='https://github.com/LakoMoor/open-pocket-ws', category='console', systems='WonderSwan / WonderSwan Color', sdram=True),
 dict(name='MSXHeroTN', repo='https://www.msx.org/fr/node/70265', category='computer', systems='MSX2+ (Tang Nano 20K)', sdram=True),
]

PROVEN = {'NESTang':'nand2mario/nestang runs on Tang Nano 20K','SNESTang':'nand2mario/snestang runs on Tang Nano 20K (ROM size limit)',
          'Open Pocket GBC':'Same author as MiSTang; its release bitstream loads on this Tang Nano 20K (DONE flag verified over JTAG)','Open Pocket WS':'Sister project built for this board (not re-verified here)','MSXHeroTN':'MSX2+ for Tang Nano 20K'}
NO = {'PSX','Saturn','N64','MegaCD','S32X','NeoGeo','DVD','Jaguar','GBA2P','Gameboy2P','SGB','3DO','PSX2P','Amiga','AmigaAGA','ao486','ao486_Tang','Minimig','X68000','PC98','PC88','MacPlus','Archimedes','AtariST','Atari-ST','Apple-IIgs','AppleIIgs','Mega-CD','CDi','CD-i','AliceMK2','Vectrex_old','Palm','TI-99_4A_x'}
LIKELY_KW = ['Atari','Coleco','SG-1000','Intellivision','Odyssey','Channel F','Astrocade','Arcadia','Vectrex','Pong','PV-1000','Gamate','CreatiVision','Pokémon Mini','Lynx','WonderSwan','Master System','Game Gear','SMS','Chip','Arduboy','Adventure Vision','My Vision','Epoch','Game of Life','Flappy','Chess','Slug','Scramble','Casio','Bally','Videopac','G7000','Supervision','Gamate','Game Boy','Game & Watch','PC Engine','TurboGrafx','Famicom','NES','Sinclair','ZX81','Spectrum','VIC-20','Apple I','Apple II','Acorn','Atom','TRS-80','Oric','Jupiter','Galaksija','Laser','ORAO','Ondra','Specialist','Vector-06','Radio-86','Mikro','KC','Pet','PET','Ti-99','TI-99','MC-10','CoCo','Dragon','Aquarius','Tatung','SAM','Sord','Multi8','MSX','SVI','BK0011','Elektronika','Tandy','UK101','Ace','Lviv','Pecom','Pmd','Tsconf','Vic','C16','Plus4','Amstrad','CPC','Microbee','Memotech','Camputers','Exidy','Kaypro','Mattel','Aquarius','Spectravideo','Sharp','MZ','Interact','Robotron','CoCo2']
MAYBE_KW = ['C64','Commodore 64','Genesis','Mega Drive','MegaDrive','TurboGrafx','PC Engine','Neo','Atari ST','Amstrad','BBC','Apple','Macintosh','Game Boy Advance','GBA','Atari 800','Atari800','Sinclair QL','Minimig','Pocket','Wonderswan','Nintendo DS']

def tier(c):
    n = c['name']; s = c['systems']
    if n in PROVEN: return 'proven', PROVEN[n]
    if n in NO or c['name'] in ('MegaCD',): return 'no', 'Too large for 20K LUT4 / 8 MB SDRAM (or needs disc/CD streaming).'
    if c['category']=='arcade':
        big = re.search(r'(Capcom|CPS|Neo|Konami GX|System ?16|System ?1[89]|Taito F[23]|68000|68K|Toaplan|NMK|Irem M|Data East|Seibu|Sega|Namco System|Williams|Midway Y|Raiden|Gauntlet|Mortal|Bubble Bobble|Rampage)', n+' '+s)
        if c.get('sdram') or big: return 'maybe','Arcade core; depends on ROM size and number of CPUs. Needs per-game fit check.'
        return 'likely','Small 8-bit arcade board: ROM into SDRAM from SD, video via the shared HDMI scaler.'
    if n in ('Atari7800','Atari5200','AtariLynx','Gamate','GameBoy','NES','SMS','TGFX16','Vectrex','ColecoVision'): return 'likely','Small enough; core-specific bring-up needed.'
    if any(k.lower() in (n+' '+s).lower() for k in ['genesis','mega drive','megadrive','c64','commodore 64','pc engine','turbografx','gba','game boy advance','atari 800','atari800','amstrad','bbc','apple','neo','st ']): return 'maybe','Fits only after trimming (no CD/expansion, reduced audio, simple scaler). Research item.'
    if c['category'] in ('computer','console','other'): return 'likely','8-bit class system; fits the 20K LUT budget in principle.'
    return 'maybe',''

MISTANG={'Open Pocket GBC':'mistang-core-gbc','Open Pocket WS':'mistang-core-ws','Chip8':'mistang-core-chip8','Pong':'mistang-core-pong','AY-3-8500':'mistang-core-pong','Apple-I':'mistang-core-apple1','Apple I':'mistang-core-apple1'}
for c in cores:
    if c['name'] in MISTANG: c['mistang']='https://github.com/MiSTang-FPGA/'+MISTANG[c['name']]
    t, why = tier(c); c['tier']=t; c['note']=why
    c['id'] = re.sub(r'[^a-z0-9]+','-',c['name'].lower()).strip('-')
seen=set(); uniq=[]
for c in cores:
    if c['id'] in seen: continue
    seen.add(c['id']); uniq.append(c)
# --- items from the user's project list (cores/xlsx_items.json): not assessed, except obviously oversized systems
xp = ref.parent / 'cores' / 'xlsx_items.json'
if xp.exists():
    norm = lambda t: re.sub(r'[^a-z0-9]+', '', t.lower())
    have = {norm(c['name']) for c in uniq}
    GAMEISH = {'Аркадные устройства': 'arcade', 'Карманные устройства': 'console', 'Игровые платформы': 'console'}
    COMP = {'Компьютеры и рабочие станции', 'Советские и восточноевропейские компьютеры', 'Домашние компьютеры', 'Европейские компьютеры',
            'Ранние компьютеры', 'Японские компьютеры', 'Исторические мини-компьютеры', 'Рабочие станции', 'Органайзеры и КПК'}
    HEAVY = ('x68000', 'amiga 1200', 'archimedes', '1040st', 'lisa', 'macintosh', 'sh-3', 'vexriscv', 'linux', 'z486', '486', 'pentium', 'sparc',
             'sgi', 'nextstation', 'playstation', 'nintendo 64', 'saturn', 'dreamcast', 'xbox', '3do', 'jaguar', 'workstation')
    for it in json.loads(xp.read_text()):
        if norm(it['name']) in have: continue
        have.add(norm(it['name']))
        cat = GAMEISH.get(it['group']) or ('computer' if it['group'] in COMP else 'other')
        heavy = any(k in it['name'].lower() for k in HEAVY)
        search = it['url_kind'].startswith('Поиск')
        uniq.append(dict(name=it['name'], repo=it['url'], category=cat, systems=it['group'] + (' · ' + it['kind'] if it['kind'] else ''), sdram=False,
                         tier='no' if heavy else 'idea', source='list', link_is_search=search,
                         note=('Too large for 20K LUT4 (estimate).' if heavy else 'From the project list; not assessed yet.') + (' Link is a GitHub search, not a repository.' if search else ' Link from the list, not re-checked.'),
                         id='list-' + norm(it['name'])))
order={'proven':0,'likely':1,'maybe':2,'idea':3,'no':4}
uniq.sort(key=lambda c:(order[c['tier']],c['category'],c['name'].lower()))
out.write_text(json.dumps(uniq,ensure_ascii=False,indent=1))
from collections import Counter
print(len(uniq), Counter(c['tier'] for c in uniq), Counter(c['category'] for c in uniq))
