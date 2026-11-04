#!/usr/bin/env python3
"""Turn an Open Pocket GBC checkout into the MiSTang launcher gateware (in place).
Adds one inout pin, reconfig_n (Tang Nano 20K pin 9), driven low while ctrl[31] is set.
usage: apply.py <opg-tree>"""
import pathlib, re, sys

root = pathlib.Path(sys.argv[1])
top = root / 'rtl/top/gbc_top.sv'
s = top.read_text()
if 'reconfig_n' in s:
    sys.exit('already patched')
s, n1 = re.subn(r'(module gbc_top \(\n)',
                r'\1    inout             reconfig_n,   // MiSTang: pull low = reload from the multiboot address\n', s, count=1)
s, n2 = re.subn(r"(assign ws2812\s*= 1'b0;\n)",
                r"\1assign reconfig_n = ctrl[31] ? 1'b0 : 1'bz;   // firmware: REG_CTRL bit 31\n", s, count=1)
if n1 != 1 or n2 != 1:
    sys.exit('gbc_top.sv layout changed, patch by hand')
top.write_text(s)

cst = root / 'rtl/board/tangnano20k.cst'
c = cst.read_text()
if 'reconfig_n' in c:
    sys.exit('cst already has reconfig_n')
cst.write_text(c.rstrip('\n') + '\nIO_LOC "reconfig_n" 9;\nIO_PORT "reconfig_n" IO_TYPE=LVCMOS33 PULL_MODE=UP;\n')
print('patched', top, 'and', cst)
