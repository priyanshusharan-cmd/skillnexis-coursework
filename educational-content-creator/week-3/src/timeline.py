"""Turns a beat sheet (narration sentence + on-screen actions) into the editor page's event timeline.
Every 'run' executes the program for real (engine.run_python), so all output and tracebacks on screen are genuine."""
import os
from engine import run_python
CODE_Y0, LINE_H, TERM_Y0, TERM_LH = 134, 44.8, 698, 36.25     # editor.html geometry: code line 1 top, line height, terminal line 1 top

def code_y(n): return CODE_Y0 + (n - 1) * LINE_H
def edit_split(old, new):
    i = 0
    while i < min(len(old), len(new)) and old[i] == new[i]: i += 1
    j = 0
    while j < min(len(old), len(new)) - i and old[-1 - j] == new[-1 - j]: j += 1
    return new[:i], new[i:len(new) - j], new[len(new) - j:]

def build(beats, times, ends, files):
    """beats: [(sentence, [action dicts])]; times/ends: sentence start/end seconds in the voice track."""
    ev, code, cur, term_lines = [], "", None, []
    for (sent, acts), t0, t1, nxt in zip(beats, times, ends, list(times[1:]) + [ends[-1] + 1.5]):
        for a in acts:
            t = t0 + a.get("at", 0); until = t + a["dur"] if "dur" in a else nxt + .05; k = a["do"]
            if k == "file": cur, code = a["name"], a["text"]; ev.append(dict(t=t, type="file", file=cur, text=code))
            elif k == "edit":
                pre, mid, post = edit_split(code, a["text"]); ev.append(dict(t=t, type="type", base=pre, text=mid, after=post, cps=a.get("cps", 18))); code = a["text"]
                assert len(mid) / a.get("cps", 18) < (nxt - t) + .5, f"typing too slow for: {sent}"
            elif k == "run":
                out = run_python(cur, code); ev.append(dict(t=t, type="run", cmd=f"python3 {cur}", out=out)); a["_out"] = out
            elif k == "clear": ev.append(dict(t=t, type="clear"))
            elif k == "hl": ev.append(dict(t=t, type="hl", line=a["line"], until=until))
            elif k == "mark": ev.append(dict(t=t, type="mark", text=a["text"], until=until))
            elif k == "callout": ev.append(dict(t=t, type="callout", text=a["text"], x=a["x"], y=a["y"], up=a.get("up", False), down=a.get("down", False), until=until))
            elif k == "ring": ev.append(dict(t=t, type="ring", x=a["x"], y=a["y"], w=a["w"], h=a["h"], until=until))
            elif k == "scroll": ev.append(dict(t=t, type="scroll", lines=a["lines"], until=until))
            elif k == "zoom": ev.append(dict(t=t, type="zoom", s=a["s"], x=a["x"], y=a["y"], dur=a.get("ease", .7)))
    ev.sort(key=lambda e: e["t"]); return {"file": files[0], "files": files, "events": ev}
