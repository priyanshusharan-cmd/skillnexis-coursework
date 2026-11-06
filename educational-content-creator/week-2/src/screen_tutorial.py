"""Task 1: 3-minute screen-recording tutorial, "How to read a Python error message" (Loom style: screen + face bubble).
The editor and terminal are a replica page driven frame by frame (OBS/Loom need a desktop session, which this
environment doesn't have); every program on screen is executed for real and its genuine output/traceback is shown.
    python src/screen_tutorial.py  -> exports/screen-tutorial.mp4, exports/screen-tutorial.srt"""
import json, sys
sys.path.insert(0, "src")
from engine import voice, capture, pip, mix, srt, loudness, B
from timeline import build, code_y
from presenter import render
G1 = 'scores = [72, 85, 90]\ntotal = sum(scores)\naverage = totl / len(scores)\nprint("Average: " + average)\n'
G2 = G1.replace("totl /", "total /"); G3 = G2.replace('print("Average: " + average)', 'print("Average:", average)')
R1 = 'def average(scores):\n    return sum(scores) / len(scores)\n\ndef report(name, scores):\n    print(name, "average:", average(scores))\n\nreport("Aarav", [72, 85, 90])\nreport("Meera", [])\n'
R2 = R1.replace("def average(scores):\n", "def average(scores):\n    if not scores:\n        return 0\n")
C = lambda text, line, dx=0, **k: dict(do="callout", text=text, x=1060 + dx, y=code_y(line) - 8, **k)
T = lambda text, y, x=1000, **k: dict(do="callout", text=text, x=x, y=y, up=True, **k)
BEATS = [
 ("Error messages look scary, but every Python error follows the same pattern.", [dict(do="file", name="grades.py", text=G1)]),
 ("Once you know where to look, you can fix most of them in under a minute.", []),
 ("In this video, we'll read three real errors together: a name error, a type error, and a longer traceback that runs through two functions.", []),
 ("Here's a tiny program that averages three test scores. Let's run it.", [dict(do="run", at=2.6)]),
 ("That block of red and white text is called a traceback. The trick is to read it from the bottom up.", [dict(do="ring", x=380, y=652, w=1180, h=380, at=1.0)]),
 ("Python prints the oldest step at the top, and the most recent one at the bottom, so the bottom is where things broke.", []),
 ("The last line tells you what went wrong. Name error. The name t o t l is not defined.", [dict(do="mark", text="NameError: name 'totl' is not defined")]),
 ("Python even suggests a fix. Did you mean, total?", [dict(do="mark", text="Did you mean: 'total'?"), dict(do="callout", text="Python suggests the fix", x=1000, y=580, down=True)]),
 ("Now go up one line. It shows the exact code, and the little arrows point right at the problem.", [dict(do="mark", text="^^^^")]),
 ("Above that, you get the file name and the line number. Line three.", [dict(do="mark", text="line 3"), dict(do="hl", line=3, at=1.5), C("Line 3", 3, at=1.5)]),
 ("So it's just a typo. Let's fix it, and run again.", [dict(do="edit", text=G2, at=1.6, cps=6), dict(do="run", at=3.4)]),
 ("A new error. That's progress, not failure.", []),
 ("Fixing one problem lets Python run further, and find the next one.", []),
 ("Bottom line first, again. Type error. Can only concatenate str, not float, to str.", [dict(do="mark", text='TypeError: can only concatenate str (not "float") to str')]),
 ("In plain words, you can't glue text and a number together with a plus sign.", [dict(do="callout", text="text + number = TypeError", x=1000, y=580, down=True)]),
 ("The arrows point at the plus, on line four.", [dict(do="hl", line=4), C("the + on line 4", 4)]),
 ("One fix: pass both values to print, separated by a comma. Print adds the space for you.", [dict(do="edit", text=G3, at=.8, cps=12), dict(do="hl", line=4, at=.8)]),
 ("Run it, and it works.", [dict(do="run", at=.4)]),
 ("You could also convert the number with s t r, but the comma is simpler, and easier to read.", []),
 ("Longer programs give longer tracebacks. Here, report calls average, and we call report twice.", [dict(do="clear"), dict(do="file", name="report.py", text=R1), dict(do="hl", line=5, at=2.2, dur=2.2), dict(do="hl", line=7, at=4.6)]),
 ("Let's run it.", [dict(do="run", at=.2)]),
 ("First, the good news. The first line printed fine, so the call for Aarav worked.", [dict(do="scroll", lines=4), dict(do="mark", text="Aarav average: 82.33333333333333")]),
 ("Also notice that recent Python versions underline the exact part of each line, with tildes and carets.", [dict(do="mark", text="~~~~~~~~~~~~^~~~~~~~~~~~~")]),
 ("Now the bottom line. Zero division error. Division by zero.", [dict(do="mark", text="ZeroDivisionError: division by zero")]),
 ("Each pair of lines above it is one step in the chain of calls. The lowest one is where it crashed: inside average, on line two.", [dict(do="mark", text="line 2, in average", at=3.5), dict(do="hl", line=2, at=3.5)]),
 ("The top one is where it started. Line eight, the call for Meera, with an empty list.", [dict(do="scroll", lines=4), dict(do="mark", text="line 8, in <module>"), dict(do="hl", line=8, at=1.5), C("empty list!", 8, dx=40, at=2.5)]),
 ("An empty list has a length of zero, so we divided by zero. The real bug isn't in average. It's the data we passed in.", []),
 ("Let's guard against it. If the list is empty, return zero.", [dict(do="edit", text=R2, at=1.0, cps=16), dict(do="hl", line=2, at=1.0)]),
 ("Run it again. Both reports work now.", [dict(do="run", at=.3)]),
 ("So, to read any Python error: start at the last line for the type and the message.", [dict(do="clear"), T("1. Last line: type + message", 700, 420)]),
 ("Then go up to find the file and the line. And in a long traceback, follow the chain until you reach your own code.", [T("2. Go up: file + line", 800, 420), T("3. Follow the chain to your code", 900, 420, at=3.2)]),
 ("And if you're ever stuck, search for the last line of the error. Someone has almost certainly seen it before.", []),
 ("Now pause the video, break the program on purpose, and see if you can predict the fix from the traceback.", []),
]
if __name__ == "__main__":
    dur, subs = voice([b[0] for b in BEATS], f"{B}/screen_vo.wav")
    tl = build(BEATS, [s[0] for s in subs], [s[1] for s in subs], ["grades.py", "report.py"])
    json.dump(tl, open(f"{B}/screen_tl.json", "w"), indent=1)
    if "--preview" in sys.argv: print("duration", round(dur, 1)); sys.exit()
    capture({"page": "src/editor.html", "kind": "editor", "tl": tl, "dur": dur, "fps": 15}, f"{B}/screen_raw.mp4")
    render(f"{B}/screen_vo.wav", f"{B}/screen_cam.mp4", mode="cam")
    pip(f"{B}/screen_raw.mp4", f"{B}/screen_cam.mp4", f"{B}/screen_pip.mp4", pos="tr", size=300)
    mix(f"{B}/screen_pip.mp4", f"{B}/screen_vo.wav", "exports/screen-tutorial.mp4")
    srt(subs, "exports/screen-tutorial.srt"); print("screen tutorial", round(dur, 1), "s", loudness("exports/screen-tutorial.mp4"), "LUFS")
