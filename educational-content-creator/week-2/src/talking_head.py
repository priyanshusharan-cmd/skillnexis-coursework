"""Task 3: talking-head explainer, "What is an algorithm? (Explained with chai)".
Medium shot, presenter on the right third, eyes on the top third line, three-point lighting (see presenter.py and
docs/lighting-and-audio.md). On-screen keywords appear on the left as each idea is spoken; lower third on first
appearance. Voice: cleaned (high-pass, gentle compression) and normalised to -14 LUFS, no music, so the voice carries.
    python src/talking_head.py  -> exports/talking-head.mp4, exports/talking-head.srt"""
import json, os, subprocess, sys
sys.path.insert(0, "src")
from engine import voice, mix, srt, loudness, B
from presenter import render
F = "/usr/share/fonts/opentype/inter/"
LINES = ["What exactly is an algorithm? It sounds complicated, but you already use them every day.",
         "An algorithm is just a precise list of steps that solves a problem.",
         "Think about making chai.",
         "Boil a cup of water. Add one spoon of tea leaves. Add sugar, and simmer for two minutes.",
         "Pour in the milk, bring it back to a boil, then strain it into a cup.",
         "That's an algorithm. And notice three things about it.",
         "First, it's precise. One spoon is clear. Some tea is not, and a computer can't guess.",
         "Second, the order matters. Straining before you boil gives you a very sad cup of chai.",
         "Third, it finishes. There's a clear last step, so you know when you're done.",
         "Programs work the same way. When you write code, you're writing a recipe for the computer, one precise step at a time.",
         "So next time you follow a recipe, ask yourself: could a computer follow this?",
         "I'm Mina, and this is Code in Small Steps. See you in the next lesson."]
# on-screen text per sentence index: (text, size, colour, y, keep_until_sentence)
TEXT = {0: [("What is an", 60, "0x5B6474", 250, 1), ("algorithm?", 120, "0x14213D", 320, 1)],
        1: [("A precise list of steps", 66, "0x14213D", 300, 2), ("that solves a problem", 66, "0xE8590C", 390, 2)],
        3: [("1  Boil a cup of water", 50, "0x14213D", 260, 5), ("2  Add 1 spoon of tea", 50, "0x14213D", 330, 5), ("3  Sugar, simmer 2 min", 50, "0x14213D", 400, 5)],
        4: [("4  Milk, boil again", 50, "0x14213D", 470, 5), ("5  Strain into a cup", 50, "0x14213D", 540, 5)],
        6: [("Precise", 96, "0xE8590C", 280, 9)], 7: [("Ordered", 96, "0x2F6DB5", 400, 9)], 8: [("Finite", 96, "0x2B8A3E", 520, 9)],
        9: [("Code = a recipe", 80, "0x14213D", 330, 11), ("for the computer", 80, "0xE8590C", 430, 11)]}
if __name__ == "__main__":
    dur, subs = voice(LINES, f"{B}/th_vo.wav", gap=.55)
    if not os.path.exists(f"{B}/th_raw.mp4") or "--force" in sys.argv: render(f"{B}/th_vo.wav", f"{B}/th_raw.mp4", mode="full")
    n = [0]
    def tf(s): n[0] += 1; p = f"{B}/th_{n[0]}.txt"; open(p, "w").write(s); return p
    vf = []
    for k, items in TEXT.items():
        for j, (txt, size, col, y, until) in enumerate(items):
            a = subs[k][0] + .15 * j; b = subs[until][0] - .05 if until < len(subs) else dur
            x = f"'if(lt(t,{a}+0.35),140-60*pow(1-(t-{a})/0.35,3),140)'"
            vf.append(f"drawtext=fontfile={F}InterDisplay-ExtraBold.otf:textfile={tf(txt)}:fontsize={size}:fontcolor={col}:x={x}:y={y}:"
                      f"alpha='if(lt(t,{a}),0,if(lt(t,{a}+0.3),(t-{a})/0.3,if(lt(t,{b}-0.25),1,max(0,({b}-t)/0.25))))':enable='between(t,{a},{b})'")
    a0 = subs[0][0] + .4                                               # lower third, first 4.5 s
    vf += [f"drawbox=x='if(lt(t,{a0}+0.4),-700+760*(1-pow(1-(t-{a0})/0.4,3)),60)':y=830:w=620:h=130:color=0x14213D@0.95:t=fill:enable='between(t,{a0},{a0}+4.5)'",
           f"drawbox=x='if(lt(t,{a0}+0.4),-700+760*(1-pow(1-(t-{a0})/0.4,3)),60)':y=830:w=12:h=130:color=0xE8590C:t=fill:enable='between(t,{a0},{a0}+4.5)'",
           f"drawtext=fontfile={F}InterDisplay-Bold.otf:textfile={tf('Mina')}:fontsize=50:fontcolor=white:x=100:y=845:enable='between(t,{a0}+0.3,{a0}+4.5)'",
           f"drawtext=fontfile={F}Inter-Medium.otf:textfile={tf('Host, Code in Small Steps')}:fontsize=30:fontcolor=0xFFD8B8:x=100:y=908:enable='between(t,{a0}+0.3,{a0}+4.5)'",
           f"fade=t=in:d=0.4,fade=t=out:st={dur - .6}:d=0.6,format=yuv420p"]
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", f"{B}/th_raw.mp4", "-vf", ",".join(vf), "-c:v", "libx264", "-crf", "18", "-preset", "veryfast", "-pix_fmt", "yuv420p", f"{B}/th_txt.mp4"], check=True)
    mix(f"{B}/th_txt.mp4", f"{B}/th_vo.wav", "exports/talking-head.mp4"); srt(subs, "exports/talking-head.srt")
    json.dump({"duration": dur, "lufs": loudness("exports/talking-head.mp4")}, open(f"{B}/th_stats.json", "w")); print("talking head", round(dur, 1), "s")
