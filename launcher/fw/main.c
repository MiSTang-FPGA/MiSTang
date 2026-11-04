// MiSTang launcher firmware (GPL-3.0, built on the Open Pocket GBC menu CPU).
// Lists /MiSTang/cores/*.json on the SD card, copies the chosen <id>.bin into flash slot A
// (changed 4 KB sectors only), verifies it and pulls RECONFIG_N: the FPGA reloads from the
// multiboot address in the launcher's own bitstream header (0x400000).
#include <string.h>
#include "ff.h"
#include "osd.h"
#include "util.h"

#define FW_VERSION   "0.1"
#define SLOT_A       0x400000u
#define SLOT_MAX     0x100000u
#define REG_SECTOR   0x200000u          // registry: last core written
#define BUF          0x000000u          // SDRAM staging buffer (the launcher has no cartridge)
#define C_RECONFIG   (1u << 31)         // ctrl[31] drives RECONFIG_N low (launcher.patch)
#define MAX_CORES    64
#define REG_MAGIC    0x4754534Du        // "MSTG"

typedef struct { char id[20], name[28]; uint32_t size; } core_t;
typedef struct { uint32_t magic; char id[20]; uint32_t size, sum; } registry_t;

static FATFS    fs;
static core_t   cores[MAX_CORES];
static int      ncores, sd_ok_mounted;
static uint32_t ctrl;
static registry_t reg;

static void ctrl_write(void) { REG_CTRL = ctrl; }
static uint32_t sum32(const void *p, uint32_t n) {
    const uint8_t *b = p; uint32_t s = 0x811C9DC5u;
    while (n--) s = (s ^ *b++) * 16777619u;
    return s;
}

// ---- tiny JSON field readers: flat objects written by tools/mkcore.py / Studio
static const char *jfind(const char *j, const char *key) {
    char pat[24]; sfmt(pat, sizeof pat, "\"%s\"", key);
    const char *p = strstr(j, pat);
    if (!p || !(p = strchr(p + strlen(pat), ':'))) return 0;
    while (*++p == ' ') ;
    return p;
}
static int jstr(const char *j, const char *key, char *out, int n) {
    const char *p = jfind(j, key);
    if (!p || *p != '"') return -1;
    int i = 0;
    for (p++; *p && *p != '"' && i < n - 1; p++) out[i++] = *p;
    out[i] = 0;
    return 0;
}
static uint32_t jnum(const char *j, const char *key) {
    const char *p = jfind(j, key);
    uint32_t v = 0;
    while (p && *p >= '0' && *p <= '9') v = v * 10 + (*p++ - '0');
    return v;
}

// the id becomes a file name: lowercase letters, digits, - and _ only
static int safe_id(const char *s) {
    if (!*s) return 0;
    for (; *s; s++) if (!((*s >= 'a' && *s <= 'z') || (*s >= '0' && *s <= '9') || *s == '-' || *s == '_')) return 0;
    return 1;
}

// ---- storage
static int mount(void) {
    if (sd_init() != 0) { logf("sd: no card\n"); return 0; }
    FRESULT r = f_mount(&fs, "", 1);
    logf("sd: %u MB, mount %d\n", sd_sectors() / 2048, r);
    return r == FR_OK;
}

static void scan(void) {
    DIR d; FILINFO fi; static char js[512];
    ncores = 0;
    if (f_opendir(&d, "/MiSTang/cores") != FR_OK) return;
    while (ncores < MAX_CORES && f_readdir(&d, &fi) == FR_OK && fi.fname[0]) {
        int l = strlen(fi.fname);
        if (l < 6 || strcmp(fi.fname + l - 5, ".json") != 0 || (fi.fattrib & AM_DIR)) continue;
        FIL f; UINT br = 0; char path[64];
        sfmt(path, sizeof path, "/MiSTang/cores/%s", fi.fname);
        if (f_open(&f, path, FA_READ) != FR_OK) continue;
        f_read(&f, js, sizeof js - 1, &br); f_close(&f); js[br] = 0;
        core_t *c = &cores[ncores];
        if (jstr(js, "id", c->id, sizeof c->id) || !safe_id(c->id)) continue;
        if (jstr(js, "name", c->name, sizeof c->name)) strcpy(c->name, c->id);
        c->size = jnum(js, "size");
        ncores++;
    }
    f_closedir(&d);
    for (int i = 1; i < ncores; i++) {            // insertion sort by name
        core_t t = cores[i]; int j = i - 1;
        while (j >= 0 && strcmp(cores[j].name, t.name) > 0) { cores[j + 1] = cores[j]; j--; }
        cores[j + 1] = t;
    }
}

// ---- UI
static void header(const char *title) {
    osd_clear(AT(CL_WHITE, CL_NAVY));
    osd_pill(1, 1, OSD_W - 2, CL_BLUE, CL_NAVY);
    osd_text(3, 1, "MiSTang", AT(CL_WHITE, CL_BLUE));
    osd_rtext(OSD_W - 3, 1, title, AT(CL_LIGHT, CL_BLUE));
}
static void message(const char *a, const char *b, uint8_t col) {
    header("launcher");
    osd_text(4, 10, a, AT(col, CL_NAVY));
    osd_text(4, 12, b, AT(CL_LIGHT, CL_NAVY));
    osd_present();
    lcd_clear(AT(CL_WHITE, CL_NAVY));
    lcd_textn(0, 4, a, 16, AT(col, CL_NAVY));
    lcd_present();
}
static void progress(const char *what, const char *name, uint32_t done, uint32_t total) {
    header(what);
    osd_text(4, 9, name, AT(CL_WHITE, CL_NAVY));
    int w = OSD_W - 8, fill = total ? (int)((uint64_t)w * done / total) : 0;
    for (int i = 0; i < w; i++) osd_put(4 + i, 12, ' ', AT(CL_BLACK, i < fill ? CL_GREEN : CL_PANEL));
    char s[16]; sfmt(s, sizeof s, "%d%%", total ? (int)((uint64_t)100 * done / total) : 0);
    osd_text(4, 14, s, AT(CL_LIGHT, CL_NAVY));
    osd_present();
}

static uint32_t held;
static uint32_t keys(void) {                 // newly pressed keys
    uint32_t cur = REG_IN & 0xFFFF;
    if (cur == held) { REG_WAIT = 200; (void)REG_WAIT; cur = REG_IN & 0xFFFF; }
    uint32_t p = cur & ~held;
    held = cur;
    return p;
}

static void draw_list(int sel, int top, const char *status) {
    header(ncores ? "choose a core" : "no cores");
    for (int r = 0; r < 15 && top + r < ncores; r++) {
        int i = top + r, y = 4 + r;
        uint8_t at = i == sel ? AT(CL_BLACK, CL_WHITE) : AT(CL_WHITE, CL_NAVY);
        if (i == sel) osd_fill(2, y, OSD_W - 4, ' ', at);
        osd_textn(4, y, cores[i].name, 24, at);
        char s[12]; sfmt(s, sizeof s, "%u KB", cores[i].size >> 10);
        osd_rtext(OSD_W - 4, y, s, i == sel ? at : AT(CL_GREY, CL_NAVY));
        if (reg.magic == REG_MAGIC && !strcmp(reg.id, cores[i].id))
            osd_put(3, y, '*', i == sel ? at : AT(CL_YELLOW, CL_NAVY));
    }
    if (!ncores) {
        osd_text(4, 8, sd_ok_mounted ? "Put cores in /MiSTang/cores/" : "No SD card", AT(CL_YELLOW, CL_NAVY));
        osd_text(4, 10, "Studio > SD card prepares one.", AT(CL_LIGHT, CL_NAVY));
    }
    osd_text(3, 21, status, AT(CL_LIGHT, CL_NAVY));
    osd_text(3, 22, "A: start   Y: rescan   * = in flash", AT(CL_GREY, CL_NAVY));
    osd_present();
    lcd_clear(AT(CL_WHITE, CL_NAVY));
    if (ncores) {
        lcd_textn(0, 2, cores[sel].name, 16, AT(CL_WHITE, CL_NAVY));
        lcd_text(0, 10, "A: start", AT(CL_LIGHT, CL_NAVY));
    }
    lcd_present();
}

// ---- boot a core
// Gowin .bin: 0xFF padding, A5 C3, header words. Only GW2A-18 (IDCODE 0x0000081B) is accepted.
static int check_bitstream(const uint8_t *b, uint32_t n) {
    uint32_t p = 0;
    while (p < n && p < 64 && b[p] == 0xFF) p++;
    if (p + 2 >= n || b[p] != 0xA5 || b[p + 1] != 0xC3) return -1;
    for (uint32_t i = p; i + 8 < n && i < p + 64; i++)
        if (b[i] == 0x06 && b[i + 4] == 0 && b[i + 5] == 0 && b[i + 6] == 0x08 && b[i + 7] == 0x1B) return 0;
    return -2;
}

static void fail(const char *a, const char *b, uint32_t ms) { message(a, b, CL_RED); wait_ms(ms); }

static int boot_core(const core_t *c) {
    char path[48]; FIL f; UINT br;
    sfmt(path, sizeof path, "/MiSTang/cores/%s.bin", c->id);
    if (f_open(&f, path, FA_READ) != FR_OK) { fail("Can't open core file", path, 1800); return -1; }
    uint32_t size = f_size(&f);
    if (size < 4096 || size > SLOT_MAX) { f_close(&f); fail("Core size out of range", "must be 4 KB .. 1 MB", 1800); return -1; }
    for (uint32_t o = 0; o < size; o += 0x10000) {
        progress("reading SD", c->name, o, size);
        uint32_t n = size - o < 0x10000 ? size - o : 0x10000;
        if (f_read(&f, (void *)sdram(BUF + o), n, &br) != FR_OK || br != n) { f_close(&f); fail("SD read error", c->name, 1800); return -1; }
    }
    f_close(&f);
    int bad = check_bitstream((const uint8_t *)sdram(BUF), size);
    if (bad) { fail(bad == -1 ? "Not a Gowin bitstream" : "Not for GW2A-18", c->id, 2200); return -1; }

    uint32_t sum = sum32((const void *)sdram(BUF), size);
    int same = reg.magic == REG_MAGIC && !strcmp(reg.id, c->id) && reg.size == size && reg.sum == sum;
    if (!same) {
        // invalidate first: a power loss mid-copy must not leave a registry entry pointing at half a core
        flash_erase_range(REG_SECTOR, 0x1000);
        memset(&reg, 0, sizeof reg);
        for (uint32_t o = 0; o < size; o += 0x10000) {
            progress("writing flash", c->name, o, size);
            uint32_t n = size - o < 0x10000 ? size - o : 0x10000;
            flash_update_sdram(SLOT_A + o, BUF + o, n);
        }
        progress("verifying", c->name, 0, size);
        static uint8_t chk[256];
        for (uint32_t o = 0; o < size; o += 256) {
            uint32_t n = size - o < 256 ? size - o : 256;
            flash_read(SLOT_A + o, chk, n);
            if (memcmp(chk, (const void *)sdram(BUF + o), n)) { fail("Verify failed", "SD card or flash fault", 2500); return -1; }
        }
        reg.magic = REG_MAGIC; strncpy(reg.id, c->id, sizeof reg.id - 1); reg.size = size; reg.sum = sum;
        flash_write(REG_SECTOR, &reg, sizeof reg);
    }
    progress("starting", c->name, size, size);
    logf("boot %s (%u bytes, %s)\n", c->id, size, same ? "already in flash" : "copied");
    wait_ms(150);
    // RECONFIG_N low for >= 1 us; the FPGA reloads and this firmware stops existing
    ctrl |= C_RECONFIG; ctrl_write();
    for (;;) ;
}

int main(void) {
    logf("\nMiSTang launcher " FW_VERSION "\n");
    ctrl = C_CORE_RST; ctrl_write();
    flash_init();
    uint32_t id = flash_id();
    logf("flash id %06x\n", id);
    if (flash_size(id) < 0x800000u) { message("Needs 8 MB flash", "W25Q64 expected", CL_RED); for (;;) wait_ms(1000); }
    flash_read(REG_SECTOR, &reg, sizeof reg);
    if (reg.magic != REG_MAGIC) memset(&reg, 0, sizeof reg);
    ctrl &= ~(C_OSD | C_DIM); ctrl_write();

    int sel = 0, top = 0;
    sd_ok_mounted = mount();
    if (sd_ok_mounted) scan();
    for (;;) {
        if (sel >= ncores) sel = ncores ? ncores - 1 : 0;
        if (sel < top) top = sel;
        if (sel >= top + 15) top = sel - 14;
        char st[40];
        sfmt(st, sizeof st, "%d core%s on SD", ncores, ncores == 1 ? "" : "s");
        draw_list(sel, top, st);
        uint32_t k = keys();
        if ((k & K_DOWN) && sel + 1 < ncores) sel++;
        if ((k & K_UP) && sel > 0) sel--;
        if (k & K_RIGHT) sel = sel + 8 < ncores ? sel + 8 : ncores ? ncores - 1 : 0;
        if (k & K_LEFT) sel = sel > 8 ? sel - 8 : 0;
        if (k & K_Y) { sd_ok_mounted = mount(); if (sd_ok_mounted) scan(); }
        if ((k & (K_A | K_START)) && ncores) boot_core(&cores[sel]);
    }
}
