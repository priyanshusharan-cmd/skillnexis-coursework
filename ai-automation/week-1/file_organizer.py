"""Preview or organize files by extension inside one chosen directory."""
from pathlib import Path
import argparse, shutil
p=argparse.ArgumentParser(); p.add_argument("folder",type=Path); p.add_argument("--apply",action="store_true")
a=p.parse_args(); root=a.folder.expanduser().resolve()
if not root.is_dir(): raise SystemExit("Choose an existing directory")
plan=[]
for item in root.iterdir():
    if item.is_file() and item.name != Path(__file__).name:
        ext=item.suffix.lower().lstrip(".") or "no-extension"
        dest=root/ext/item.name
        if dest.parent.resolve().parent != root: raise SystemExit("Unsafe destination")
        plan.append((item,dest))
for src,dst in plan: print(f"{src.name} -> {dst.parent.name}/{dst.name}")
if a.apply:
    for src,dst in plan:
        dst.parent.mkdir(exist_ok=True); shutil.move(str(src),str(dst))
    print(f"Moved {len(plan)} files")
else: print(f"Dry run: {len(plan)} files. Review, then add --apply to move them.")
