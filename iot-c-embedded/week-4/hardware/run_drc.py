"""Runs KiCad's design-rule check on agri-node.kicad_pcb and prints a summary. Exit code 1 on errors."""
import re
import sys

import pcbnew

board = pcbnew.LoadBoard("agri-node.kicad_pcb")
pcbnew.WriteDRCReport(board, "drc.rpt", pcbnew.EDA_UNITS_MILLIMETRES, True)
text = open("drc.rpt").read()
for line in text.splitlines():
    if line.startswith("**") and "Found" in line:
        print(line)
kinds = re.findall(r"^\[(\w+)\]", text, re.M)
counts = {k: kinds.count(k) for k in sorted(set(kinds))}
print(counts)
errors = len(re.findall(r"Severity: error", text))
print("errors:", errors)
sys.exit(1 if errors else 0)
