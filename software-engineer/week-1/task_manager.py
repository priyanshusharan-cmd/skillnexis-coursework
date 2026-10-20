"""Small JSON task manager. Usage: python3 task_manager.py add "Read docs" --priority high"""
import argparse, json
from datetime import date
from pathlib import Path
STORE=Path(__file__).with_name("tasks.json")
def load(): return json.loads(STORE.read_text()) if STORE.exists() else []
def save(tasks): STORE.write_text(json.dumps(tasks,indent=2)+"\n")
def main():
    p=argparse.ArgumentParser(); sub=p.add_subparsers(dest="cmd",required=True)
    a=sub.add_parser("add"); a.add_argument("title"); a.add_argument("--priority",choices=["low","medium","high"],default="medium"); a.add_argument("--due")
    sub.add_parser("list")
    u=sub.add_parser("update"); u.add_argument("id",type=int); u.add_argument("--title"); u.add_argument("--priority",choices=["low","medium","high"]); u.add_argument("--done",action="store_true")
    d=sub.add_parser("delete"); d.add_argument("id",type=int)
    x=p.parse_args(); tasks=load()
    if x.cmd=="add":
        if not x.title.strip(): raise SystemExit("title cannot be empty")
        if x.due:
            try: date.fromisoformat(x.due)
            except ValueError: raise SystemExit("due date must be YYYY-MM-DD")
        t={"id":max([t["id"] for t in tasks],default=0)+1,"title":x.title.strip(),"priority":x.priority,"due":x.due,"done":False}; tasks.append(t); save(tasks); print(t)
    elif x.cmd=="list":
        for t in tasks: print(f"{t['id']} [{'x' if t['done'] else ' '}] {t['priority']} {t['title']} (due {t['due'] or 'none'})")
    elif x.cmd=="update":
        t=next((t for t in tasks if t["id"]==x.id),None)
        if not t: raise SystemExit("task ID not found")
        if x.title is not None and not x.title.strip(): raise SystemExit("title cannot be empty")
        if x.title is not None: t["title"]=x.title.strip()
        if x.priority: t["priority"]=x.priority
        if x.done: t["done"]=True
        save(tasks); print(t)
    else:
        before=len(tasks); tasks=[t for t in tasks if t["id"]!=x.id]
        if len(tasks)==before: raise SystemExit("task ID not found")
        save(tasks); print(f"Deleted task {x.id}")
if __name__=="__main__": main()
