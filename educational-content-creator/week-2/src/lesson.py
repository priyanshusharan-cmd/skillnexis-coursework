"""Mini project: a complete 5-minute lesson, "Python variables: labelled boxes for values" (Lesson 1 of Code in Small Steps).
Combines the 10-slide deck, screen-recorded coding (real output), the talking-head presenter (full shots for the
hook and outro, a face bubble elsewhere), background music ducked under the voice, captions; exported 1080p30.
    python src/lesson.py  -> exports/lesson-variables-1080p.mp4, exports/lesson-variables.srt"""
import json, os, subprocess, sys, wave
import numpy as np
sys.path.insert(0, "src")
from engine import voice, capture, pip, srt, loudness, VOICE_CHAIN, B, SR
from timeline import build, code_y
from presenter import render
L1 = 'age = 18\nname = "Mina"\nprice = 2.5\n'
L2 = L1 + 'print(age, name, price)\n'
L3 = L2 + 'print(type(age), type(name), type(price))\n'
L4 = L3 + 'age = 19\nprint(age)\n'
P1 = 'print(5 + 2)\nprint("5" + "2")\nprint("5" + 2)\n'; P2 = P1.replace('print("5" + 2)', 'print(int("5") + 2)')
T1 = 'a = 12\nb = 30\nprint(a + b)\nprint("The sum is", a + b)\n'
N1 = 'total_score = 95\nprint(total_score)\n'; N2 = N1.replace('total_score', 'total score')
E1 = 'score = 40\nprint(scor)\n'; E2 = 'score = 40\nprint(score)\n'
C = lambda text, line, **k: dict(do="callout", text=text, x=1040, y=code_y(line) - 8, **k)
SEG = [
 ("head", ["Why can Python add five and two, but join the text five and two into fifty two?",
           "Hi, I'm Mina, and this is Code in Small Steps.",
           "In the next five minutes, you'll learn what a variable is, the three basic types, and how to fix the most common variable error."], {}),
 ("slides", [("This is lesson one. Variables: labelled boxes for values.", 0),
             ("Here's the puzzle. Five plus two gives seven. But five plus two, in quotes, gives fifty two. Same symbol, different answer.", 1),
             ("By the end, you'll be able to create a variable, tell three types apart, predict what plus does, and fix the most common error.", 2),
             ("So, what is a variable? It's a name that points to a value.", 3),
             ("When you write age equals eighteen, Python stores the value eighteen, and puts the label age on it.", None),
             ("Think of a sticky note on a jar. The note is the name, and whatever is inside the jar is the value.", None),
             ("The equals sign means store. It does not mean, is equal to.", None)], {}),
 ("screen", [("Let's try it in the editor. I'll create three variables: an age, a name, and a price.", [dict(do="file", name="lesson.py", text=""), dict(do="edit", text=L1, at=2.4, cps=9)]),
             ("Print them, and Python looks up each label and shows its value.", [dict(do="edit", text=L2, at=.2, cps=14), dict(do="run", at=2.6)]),
             ("Now let's ask Python what type each value is, using the type function.", [dict(do="edit", text=L3, at=.3, cps=16), dict(do="run", at=3.6)]),
             ("Eighteen is an int, a whole number. Mina, in quotes, is a str, short for string. And two point five is a float.", [dict(do="mark", text="<class 'int'>", dur=2.2), dict(do="mark", text="<class 'str'>", at=2.2, dur=3), dict(do="mark", text="<class 'float'>", at=5.4)]),
             ("Variables can also change. That's why they're called variables.", []),
             ("If I set age to nineteen and print it again, the label age now points to the new value.", [dict(do="edit", text=L4, at=.4, cps=12), dict(do="run", at=3.2), dict(do="hl", line=6, at=3.2)])], {}),
 ("screen", [("One more thing before we move on: naming.", [dict(do="clear"), dict(do="file", name="names.py", text=N1)]),
             ("Names can use letters, numbers and underscores, but they can't start with a number, and they can't contain spaces.", [dict(do="hl", line=1)]),
             ("Total underscore score works fine.", [dict(do="run", at=.3)]),
             ("But if I replace the underscore with a space and run it, Python can't read the line, and stops with a syntax error.", [dict(do="edit", text=N2, at=.6, cps=12), dict(do="run", at=4.2)]),
             ("So stick to lowercase words joined by underscores. That's the standard Python style.", [dict(do="mark", text="SyntaxError: invalid syntax")])], {}),
 ("slides", [("Those are the three basic types. Ints are whole numbers. Floats have a decimal point. And strings are text, always inside quotes.", 4),
             ("And here's the answer to our puzzle. The type decides what plus does.", 5),
             ("With two ints, plus adds. With two strings, plus joins the text.", None),
             ("Mix a string and an int, and Python stops with a type error, because it won't guess what you meant.", None)], {}),
 ("screen", [("Let's prove it in a new file, with all three cases side by side.", [dict(do="clear"), dict(do="file", name="plus.py", text=""), dict(do="edit", text=P1, at=.5, cps=24)]),
             ("Run it.", [dict(do="run", at=.2)]),
             ("Seven, then fifty two, and then a type error on line three, exactly as predicted.", [dict(do="mark", text="TypeError", at=2.4), dict(do="hl", line=3, at=2.4), C("str + int", 3, at=2.4)])], {}),
 ("slides", [("To fix that, convert the type on purpose. int of five gives the number five. str of eighteen gives the text eighteen.", 6),
             ("This matters a lot, because anything a user types into input arrives as a string.", None),
             ("So if someone types twelve, Python gives you the text one two, and you convert it with int before doing any maths.", None)], {}),
 ("screen", [("Wrap the five in int, and run it again.", [dict(do="clear"), dict(do="file", name="plus.py", text=P1), dict(do="edit", text=P2, at=.8, cps=10), dict(do="run", at=2.6)]),
             ("Now the last line prints seven.", [dict(do="hl", line=3)])], {}),
 ("slides", [("Your turn. Store two numbers in two variables, and print their sum. Pause the video, or try it during this ten second timer.", 7)], {"pause": {0: 10.5}, "timer": True}),
 ("screen", [("Here's one solution. Twelve plus thirty prints forty two.", [dict(do="clear"), dict(do="file", name="try_it.py", text=T1), dict(do="run", at=2.0)]),
             ("And with a comma, you can put the result inside a sentence.", [dict(do="hl", line=4), dict(do="mark", text="The sum is 42")])], {}),
 ("slides", [("Finally, the most common error. Names must match exactly.", 8),
             ("Here, score is spelled correctly on line one, but misspelled on line two. Python raises a name error, and even suggests the right name.", None)], {}),
 ("screen", [("Let's see it for real.", [dict(do="clear"), dict(do="file", name="error.py", text=E1), dict(do="run", at=.6)]),
             ("Read the last line first. Name error, s c o r is not defined. Did you mean, score?", [dict(do="mark", text="NameError: name 'scor' is not defined")]),
             ("Fix the spelling, run again, and it prints forty.", [dict(do="edit", text=E2, at=.6, cps=8), dict(do="run", at=2.0)])], {}),
 ("slides", [("Let's recap. A variable is a name that points to a value.", 9),
             ("The type changes what operators like plus do. And you can convert types on purpose, with int, str and float.", None),
             ("And whenever a result surprises you, check the types with the type function.", None)], {}),
 ("head", ["Next lesson, we'll use variables to make decisions, with if and else.",
           "Before then, change the numbers in today's code, and predict the result before you run it.",
           "Thanks for learning with me today. If this helped, subscribe, and leave a question in the comments.",
           "See you in the next small step."], {}),
]
def fit_wav(src, dst, seconds):
    with wave.open(src) as w: x = np.frombuffer(w.readframes(w.getnframes()), np.int16)
    n = int(round(seconds * SR)); x = np.pad(x, (0, max(0, n - len(x))))[:n]
    with wave.open(dst, "wb") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(x.tobytes())
def vdur(p): return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p], capture_output=True, text=True).stdout)
if __name__ == "__main__":
    files, wavs, allsubs, t0, chapters = [], [], [], 0.0, []
    only = [int(a) for a in sys.argv[1:] if a.isdigit()]
    for k, (kind, items, opt) in enumerate(SEG):
        sents = items if kind == "head" else [i[0] for i in items]
        wav = f"{B}/L{k:02d}.wav"; dur, subs = voice(sents, wav, pauses=opt.get("pause"), speed=130)   # a beginner lesson: slower than the other videos
        out = f"{B}/L{k:02d}_{kind}.mp4"
        if (not os.path.exists(out)) or k in only:
            if kind == "head": render(wav, out, mode="full")
            else:
                if kind == "slides":
                    sl = [dict(i=s, start=0 if j == 0 else subs[j][0] - .2) for j, (_, s) in enumerate(items) if s is not None]
                    if opt.get("timer"): sl[0]["timer_at"] = subs[0][1] + .3
                    capture({"page": "slides/deck.html", "kind": "deck", "slides": sl, "dur": dur, "fps": 15}, f"{B}/L{k:02d}_raw.mp4")
                else:
                    tl = build(items, [s[0] for s in subs], [s[1] for s in subs], ["lesson.py", "names.py", "plus.py", "try_it.py", "error.py"])
                    capture({"page": "src/editor.html", "kind": "editor", "tl": tl, "dur": dur, "fps": 15}, f"{B}/L{k:02d}_raw.mp4")
                render(wav, f"{B}/L{k:02d}_cam.mp4", mode="cam")
                pip(f"{B}/L{k:02d}_raw.mp4", f"{B}/L{k:02d}_cam.mp4", out, pos="br" if kind == "slides" else "tr", size=220 if kind == "slides" else 300)
        vd = vdur(out); fit_wav(wav, f"{B}/L{k:02d}_fit.wav", vd)
        files.append(out); wavs.append(f"{B}/L{k:02d}_fit.wav"); allsubs += [(a + t0, b + t0, s) for a, b, s in subs]; t0 += vd
        print("segment", k, kind, round(vd, 1), flush=True)
    open(f"{B}/L_list.txt", "w").write("".join(f"file '{os.path.basename(f)}'\n" for f in files))
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", f"{B}/L_list.txt", "-c", "copy", f"{B}/L_video.mp4"], check=True)
    x = np.concatenate([np.frombuffer(wave.open(w).readframes(10 ** 9), np.int16) for w in wavs])
    with wave.open(f"{B}/L_vo.wav", "wb") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(x.tobytes())
    subprocess.run([sys.executable, "src/music.py", str(int(t0) + 5)], check=True)
    fc = (f"[1:a]{VOICE_CHAIN},aresample=44100,aformat=channel_layouts=stereo,asplit=2[v1][v2];[2:a]volume=0.4[m];"
          f"[m][v1]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=500[duck];[duck][v2]amix=inputs=2:duration=first:normalize=0:weights='0.75 1.4',"
          f"atrim=0:{t0:.3f},afade=t=out:st={t0 - 2.5}:d=2.5,loudnorm=I=-14:TP=-1.5:LRA=11[a]")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", f"{B}/L_video.mp4", "-i", f"{B}/L_vo.wav", "-i", f"{B}/music.wav", "-filter_complex", fc, "-map", "0:v", "-map", "[a]",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "exports/lesson-variables-1080p.tmp.mp4"], check=True)
    os.replace("exports/lesson-variables-1080p.tmp.mp4", "exports/lesson-variables-1080p.mp4"); srt(allsubs, "exports/lesson-variables.srt")
    json.dump({"duration": t0, "lufs": loudness("exports/lesson-variables-1080p.mp4"), "segments": [os.path.basename(f) for f in files]}, open(f"{B}/lesson_stats.json", "w"))
    print("lesson", round(t0, 1), "s")
