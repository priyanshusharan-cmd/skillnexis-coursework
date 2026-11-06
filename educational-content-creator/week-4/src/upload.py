"""Upload-ready packages for the 3 launch videos: each video gets a 20 s end-screen outro appended (its slots line up
with the YouTube end-screen elements in upload/endscreen.json), plus metadata (title, description with chapters,
tags, category, playlist, thumbnail, captions, cards).   python src/upload.py -> upload/"""
import json, os, re, shutil, subprocess
E2, E3, T3 = "../week-2/exports/", "../week-3/exports/", "../week-3/thumbnails/"
END = 20.0
CHANNEL = "Code in Small Steps"
FOOT = ("\n\nCode in Small Steps: one useful Python idea at a time, with real code you can run. New lesson every week.\n"
        "The presenter is an illustrated character and the voice is synthetic; every program and every output shown is real (Python 3.13).")
VIDEOS = [
 dict(slug="01-python-variables", src=E2 + "lesson-variables-1080p.mp4", srt=E2 + "lesson-variables.srt", thumb=T3 + "yt-variables.png",
      title='Python Variables for Beginners: Why "5" + "2" Gives "52"',
      hook='Why can Python add 5 and 2, but join "5" and "2" into "52"? In this beginner lesson you\'ll learn what a variable really is (a labelled box for a value), the three basic types (int, float, str), and how the type decides what + does.',
      chapters=[(0, "Why does \"5\" + \"2\" give \"52\"?"), (20, "What a variable is"), (67, "Creating and printing variables"), (104, "Naming rules (and a real SyntaxError)"),
                (132, "Three basic types"), (161, "Proof: 5 + 2 vs \"5\" + \"2\""), (173, "Converting types: int(), str(), float()"), (202, "Try it (10-second challenge)"),
                (222, "Solution"), (232, "The most common error: NameError"), (262, "Recap"), (281, "Practise and what is next")],
      practice="store two numbers in two variables, add them, and print the result inside a sentence. The solution is in the Solution chapter.",
      tags=["python variables", "python for beginners", "python data types", "int float str python", "python type conversion", "python typeerror", "python nameerror",
            "learn python", "python tutorial", "coding for beginners", "python course", "code in small steps"],
      playlist="Python from zero", next="02-read-python-errors", cards=[(161, "02-read-python-errors", "Errors scare you? Watch this next")]),
 dict(slug="02-read-python-errors", src=E2 + "screen-tutorial.mp4", srt=E2 + "screen-tutorial.srt", thumb=T3 + "yt-errors.png",
      title="How to Read a Python Error Message (Traceback Explained for Beginners)",
      hook="Python error messages look scary, but every one follows the same pattern. Read three real errors with me (NameError, TypeError and a ZeroDivisionError with a 3-step traceback) and learn the one habit that fixes most of them: start at the bottom line.",
      chapters=[(0, "Errors follow a pattern"), (18, "Error 1: NameError (read the last line first)"), (63, "Error 2: TypeError"), (101, "Error 3: a longer traceback"),
                (157, "The 3-step method"), (177, "Your turn")],
      practice="break a working program on purpose (misspell a name, divide by zero) and read the traceback bottom-up before fixing it.",
      tags=["python error", "python traceback", "how to read python errors", "python nameerror", "python typeerror", "zerodivisionerror python", "python debugging",
            "python for beginners", "learn python", "debugging for beginners", "code in small steps"],
      playlist="Debugging basics", next="03-python-if-else", cards=[(140, "01-python-variables", "Why \"5\" + 2 fails: the variables lesson")]),
 dict(slug="03-python-if-else", src=E3 + "if-else-long-form.mp4", srt=E3 + "if-else-long-form.srt", thumb=T3 + "yt-if-else.png",
      title="Python If Else Explained for Beginners (elif, and/or, Common Mistakes)",
      hook="Learn Python if, else and elif in about 5 minutes, with real code you can run. You'll build a grade checker, see why the ORDER of elif conditions matters, fix the two most common beginner errors (IndentationError and = vs ==), and combine conditions with and/or.",
      chapters=[(0, "Intro"), (19, "The idea"), (64, "Indentation matters"), (91, "elif: more than two choices"), (135, "Comparing values"), (169, "and / or: combining conditions"),
                (198, "Putting it together"), (235, "Try it"), (269, "Recap")],
      practice='write a program that stores an age and prints "Can vote" if it\'s 18 or more, otherwise "Not yet". The solution is at the end of the Try it chapter.',
      tags=["python if else", "python elif", "python for beginners", "if else statement python", "python conditions", "python tutorial", "learn python", "indentationerror python",
            "python comparison operators", "python and or", "coding for beginners", "code in small steps"],
      playlist="Python from zero", next="01-python-variables", cards=[(150, "02-read-python-errors", "Got an IndentationError? Read it like this")]),
]
ts = lambda s: f"{int(s) // 60}:{int(s) % 60:02d}"
def duration(p): return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p], capture_output=True, text=True).stdout)
os.makedirs("upload", exist_ok=True)
# the end-screen outro: still background, fade in, quiet music bed (original track from video-editing week 3)
if not os.path.exists("build/endscreen.mp4"):
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-framerate", "30", "-i", "build/endscreen.png", "-ss", "8", "-t", str(END), "-i", "build/beat.wav",
                    "-vf", f"format=yuv420p,loop=-1:1,trim=duration={END},fade=in:0:15", "-af", f"volume=0.25,afade=t=in:d=0.5,afade=t=out:st={END - 2}:d=2,aresample=48000",
                    "-ac", "2", "-c:v", "libx264", "-crf", "18", "-preset", "veryfast", "-pix_fmt", "yuv420p", "-r", "30", "-c:a", "aac", "-b:a", "192k", "build/endscreen.mp4"], check=True)
slugs = {v["slug"]: v for v in VIDEOS}; meta = []
for v in VIDEOS:
    out = f"upload/{v['slug']}.mp4"; d0 = duration(v["src"])
    if not os.path.exists(out):
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", v["src"], "-i", "build/endscreen.mp4", "-filter_complex",
                        "[0:a]aresample=48000[a0];[1:a]aresample=48000[a1];[0:v][a0][1:v][a1]concat=n=2:v=1:a=1[v][a]", "-map", "[v]", "-map", "[a]",
                        "-c:v", "libx264", "-crf", "18", "-preset", "veryfast", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out + ".tmp.mp4"], check=True)
        os.replace(out + ".tmp.mp4", out)
    shutil.copy(v["srt"], f"upload/{v['slug']}.en.srt"); shutil.copy(v["thumb"], f"upload/{v['slug']}-thumbnail.png")
    for (a, _), (b, _) in zip(v["chapters"], v["chapters"][1:]): assert b - a >= 10, (v["slug"], a, b)      # YouTube: chapters >= 10 s, first at 0:00
    chap = "\n".join(f"{ts(t)} {n}" for t, n in v["chapters"]); nxt = slugs[v["next"]]["title"]
    desc = f"{v['hook']}\n\nCHAPTERS\n{chap}\n\nPRACTICE: {v['practice']}\n\nWatch next: {nxt}{FOOT}\n\n#python #learnpython #codinglesson"
    tags = ", ".join(v["tags"]); assert len(tags) <= 500 and len(v["title"]) <= 100 and len(desc) <= 5000
    m = dict(file=out, thumbnail=f"upload/{v['slug']}-thumbnail.png", captions=f"upload/{v['slug']}.en.srt", title=v["title"], description=desc, tags=v["tags"],
             category="Education (27)", language="English", audience="Not made for kids", playlist=v["playlist"], license="Standard YouTube License",
             altered_or_synthetic_content="Yes: synthetic voice and illustrated presenter (declare in YouTube Studio's 'Altered content' setting)",
             duration_s=round(duration(out), 1), content_s=round(d0, 1),
             end_screen=dict(start_s=round(d0, 1), length_s=END, elements=[dict(type="video", target=v["next"], label="Next lesson", left=.078, top=.278, width=.375),
                                                                             dict(type="video", target="best_for_viewer", left=.547, top=.278, width=.375),
                                                                             dict(type="subscribe", left=.4375, top=.741, width=.125)]),
             cards=[dict(at=ts(t), video=s, teaser=x) for t, s, x in v["cards"]])
    meta.append(m); json.dump(m, open(f"upload/{v['slug']}.json", "w"), indent=1, ensure_ascii=False); print(v["slug"], m["duration_s"], "s", flush=True)
md = ["# Launch videos: upload sheet", "", "Paste these into YouTube Studio (Create → Upload video). Each file already ends with a 20 s end-screen outro; place the end-screen elements on the dashed slots (positions in each `.json`).", ""]
for m in meta:
    md += [f"## {m['title']}", "", f"* **File:** `{os.path.basename(m['file'])}` ({ts(m['duration_s'])}) · **Thumbnail:** `{os.path.basename(m['thumbnail'])}` · **Captions:** `{os.path.basename(m['captions'])}`",
           f"* **Playlist:** {m['playlist']} · **Category:** {m['category']} · **Audience:** {m['audience']}",
           f"* **End screen** from {ts(m['end_screen']['start_s'])}: next lesson (left), best for viewer (right), subscribe (centre bottom)",
           "* **Cards:** " + "; ".join(f"{c['at']} → {c['video']} (\"{c['teaser']}\")" for c in m["cards"]), f"* **Altered content:** {m['altered_or_synthetic_content']}", "",
           f"**Title** ({len(m['title'])} characters)", "```", m["title"], "```", f"**Description** ({len(m['description'])} characters)", "```", m["description"], "```",
           f"**Tags** ({len(', '.join(m['tags']))} characters)", "```", ", ".join(m["tags"]), "```", ""]
open("upload/UPLOAD-SHEET.md", "w").write("\n".join(md)); json.dump([dict(type=e["type"], left=e["left"], top=e["top"], width=e["width"]) for e in meta[0]["end_screen"]["elements"]], open("upload/endscreen.json", "w"), indent=1)
