"""Lesson 2 of Code in Small Steps: "If / else: let your program choose".
Talking-head parts are recorded as one unedited take each (pauses, flubs and restarts left in) so the edit has real
work to do; screen parts are recorded clean, and their zooms, call-outs and boxes are added in the edit (src/edit.py)."""
G1 = 'score = 72\n\nif score >= 40:\n    print("Pass")\nelse:\n    print("Fail")\n'; G2 = G1.replace("72", "35")
I0 = 'score = 72\nif score >= 40:\n    print("Pass")\n'; I1 = I0.replace('    print', 'print')
E1 = 'score = 72\n\nif score >= 90:\n    print("A")\nelif score >= 75:\n    print("B")\nelif score >= 40:\n    print("C")\nelse:\n    print("Fail")\n'
E2 = 'score = 95\n\nif score >= 40:\n    print("C")\nelif score >= 75:\n    print("B")\nelif score >= 90:\n    print("A")\nelse:\n    print("Fail")\n'
Q1 = 'score = 40\nif score = 40:\n    print("Exactly forty")\n'; Q2 = Q1.replace("score = 40:", "score == 40:")
A1 = 'age = 20\nhas_id = True\n\nif age >= 18 and has_id:\n    print("Entry allowed")\nelse:\n    print("Sorry")\n'; A2 = A1.replace("True", "False")
T1 = 'age = 15\nstudent = True\n\nif age < 5:\n    price = 0\nelif age < 18 or student:\n    price = 100\nelse:\n    price = 200\n\nprint("Ticket price:", price)\n'
T2 = T1.replace('age = 15\nstudent = True', 'age = 30\nstudent = False')
S1 = 'age = 17\n\nif age >= 18:\n    print("Can vote")\nelse:\n    print("Not yet")\n'; S2 = S1.replace("17", "18")
F = lambda name, text: dict(do="file", name=name, text=text)
E = lambda text, at=.3, cps=16: dict(do="edit", text=text, at=at, cps=cps)
R = lambda at=.3: dict(do="run", at=at)
SECTIONS = [
 dict(kind="head", id="hook", chapter="Intro", lines=[
   "What if your program could make a decision, like printing pass or fail, depending on a score?",
   "That's exactly what if and else do, and they're the reason programs feel smart.",
   "I'm Mina, this is Code in Small Steps, and by the end of this video, you'll write a grade checker that handles four different grades."],
   flubs={2: "I'm Mina, this is Code in Small Steps, and by the end of this video, you'll write a grade check, um, checker that"}),
 dict(kind="card", id="c1", num="1", title="The idea"),
 dict(kind="head", id="idea", chapter="1 · The idea", lines=[
   "An if statement asks a question that's either true or false.",
   "If the answer is true, Python runs the indented code underneath. If it's false, Python skips it.",
   "Else is the backup plan. It runs only when the condition was false.",
   "It's like the gate at a cinema. If you have a ticket, you go in. Else, you go to the ticket counter.",
   "Let's see it in code."], flubs={1: "If the answer is false, Python runs, no, wait"},
   panel=[(0, "if  condition:", "#E8590C"), (1, "    True  → runs", "#2B8A3E"), (1, "    False → skips", "#C92A2A"), (2, "else:", "#2F6DB5"), (2, "    runs when False", "#2F6DB5"), (3, "ticket? → go in, else → counter", "#5B6474")]),
 dict(kind="screen", id="demo", chapter="1 · The idea", beats=[
   ("Here's a score of seventy two.", [F("grade.py", "score = 72\n")]),
   ("If the score is at least forty, print pass. Otherwise, print fail.", [E(G1, .2, 22)]),
   ("Run it, and we get pass, because seventy two is at least forty.", [R(.4)]),
   ("Change the score to thirty five and run it again. Now the else branch runs instead.", [E(G2, 1.4, 6), R(3.0)])],
   ann=[dict(s=1, at=1.0, kind="box", line=(3, 3), label="the condition: True or False?"), dict(s=2, at=1.6, kind="term", text="Pass", label="True, so the if branch ran"),
        dict(s=3, at=4.0, kind="box", line=(5, 6), label="False, so else runs")],
   zoom=[(0, 0, 1.35, .42, .25), (2, .2, 1.0, .5, .5), (3, 0, 1.3, .42, .3), (3, 3.2, 1.0, .5, .5)]),
 dict(kind="card", id="c2", num="2", title="Indentation matters"),
 dict(kind="screen", id="indent", chapter="2 · Indentation", beats=[
   ("Notice the four spaces before print. They're not decoration.", [dict(do="clear"), F("indent.py", I0)]),
   ("In Python, indentation tells it which lines belong to the if.", []),
   ("Delete the spaces and run it, and Python refuses, with an indentation error.", [E(I1, 1.0, 20), R(2.6)]),
   ("It even tells you why: it expected an indented block after the if statement on line two.", []),
   ("Put the spaces back, and it runs again.", [E(I0, .8, 10), R(2.2)])],
   ann=[dict(s=0, at=1.2, kind="box", line=(3, 3), cols=(0, 4), label="4 spaces"), dict(s=3, at=.6, kind="term", text="IndentationError", label="Read the last line first")],
   zoom=[(0, .6, 1.5, .3, .25), (2, 2.4, 1.25, .45, .78), (4, 0, 1.0, .5, .5)]),
 dict(kind="card", id="c3", num="3", title="elif: more than two choices"),
 dict(kind="screen", id="elif", chapter="3 · elif", beats=[
   ("Pass or fail is fine, but real grades have more levels. That's what elif is for.", [dict(do="clear"), F("grades.py", "score = 72\n\n")]),
   ("Elif means, else if. Python checks each condition from top to bottom.", [E(E1, .3, 32)]),
   ("Seventy two isn't ninety or more, and it isn't seventy five or more, but it is forty or more. So we get a C.", [R(.3)]),
   ("And here's the important part. Python stops at the first condition that's true.", []),
   ("Watch what happens if I put the forty check first, and use a score of ninety five.", [F("grades.py", E2)]),
   ("Ninety five should be an A, but we get a C, because forty or more was true first, and Python never looked any further.", [R(.3)]),
   ("So always check the strictest condition first.", [F("grades.py", E1)])],
   ann=[dict(s=2, at=1.0, kind="box", line=(3, 3), label="72 ≥ 90? False"), dict(s=2, at=3.0, kind="box", line=(5, 5), label="72 ≥ 75? False"),
        dict(s=2, at=5.0, kind="box", line=(7, 7), label="72 ≥ 40? True → C"), dict(s=4, at=2.0, kind="box", line=(3, 3), label="checked first"),
        dict(s=5, at=1.0, kind="term", text="C", label="95 printed C!"), dict(s=6, at=.6, kind="box", line=(3, 3), label="strictest first")],
   zoom=[(1, 0, 1.0, .5, .5), (2, .6, 1.3, .4, .35), (4, 0, 1.3, .4, .35), (5, 3.0, 1.0, .5, .5)]),
 dict(kind="card", id="c4", num="4", title="Comparing values"),
 dict(kind="head", id="compare", chapter="4 · Comparisons", lines=[
   "Conditions usually compare two values.",
   "Double equals checks if two things are equal. An exclamation mark and equals checks if they're different.",
   "And you've got less than, greater than, and their or-equal versions.",
   "The most common mistake is using a single equals sign inside an if. Let me show you."],
   flubs={1: "Double equals checks if two things are, uh, different. No"},
   panel=[(1, "==   equal", "#14213D"), (1, "!=   not equal", "#14213D"), (2, "<   >   less / greater", "#14213D"), (2, "<=  >=  or equal", "#14213D"), (3, "=    stores (not a comparison!)", "#C92A2A")]),
 dict(kind="screen", id="eq", chapter="4 · Comparisons", beats=[
   ("Here I wrote, if score equals forty, with one equals sign.", [dict(do="clear"), F("equals.py", Q1)]),
   ("Python stops with a syntax error, and the message is brilliant. Maybe you meant double equals?", [R(.3)]),
   ("Remember, one equals sign stores a value. Two equals signs compare.", []),
   ("Add the second equals sign, and it works.", [E(Q2, .6, 6), R(1.6)])],
   ann=[dict(s=0, at=1.5, kind="box", line=(2, 2), cols=(9, 10), label="one ="), dict(s=1, at=3.0, kind="term", text="Maybe you meant '==' or ':=' instead of '='?", label="Python suggests the fix")],
   zoom=[(0, .8, 1.5, .3, .22), (1, 2.6, 1.2, .45, .78), (3, 0, 1.0, .5, .5)]),
 dict(kind="card", id="c5", num="5", title="and / or: combining conditions"),
 dict(kind="screen", id="andor", chapter="5 · and / or", beats=[
   ("One last tool. You can combine conditions, with and, and or.", [dict(do="clear"), F("entry.py", A1)]),
   ("With and, both sides must be true. Here the age is twenty, and has I D is true, so entry is allowed.", [R(4.0)]),
   ("Set has I D to false, and the whole condition becomes false, even though the age is fine.", [E(A2, 1.0, 6), R(3.2)]),
   ("With or, only one side needs to be true. That's handy for checks like, if the day is Saturday, or Sunday.", [])],
   ann=[dict(s=1, at=.8, kind="box", line=(4, 4), cols=(3, 25), label="both must be True"), dict(s=2, at=4.6, kind="term", text="Sorry", label="one side False → False")],
   zoom=[(0, .5, 1.3, .4, .3), (1, 3.6, 1.0, .5, .5), (3, 0, 1.0, .5, .5)]),
 dict(kind="card", id="c6", num="6", title="Putting it together"),
 dict(kind="screen", id="ticket", chapter="6 · Together", beats=[
   ("Let's put it all together, with a cinema ticket price.", [dict(do="clear"), F("ticket.py", T1)]),
   ("Children under five go free. Anyone under eighteen, or any student, pays a hundred. Everyone else pays two hundred.", []),
   ("Our viewer is fifteen, so the first check is false, but the elif is true. One hundred.", [R(.3)]),
   ("Now let's try an adult who isn't a student.", [E(T2, .6, 10)]),
   ("Both sides of the or are false, so we fall through to else, and pay two hundred.", [R(.3)]),
   ("The order, the or, and the else all work together. That's most of what you need for real decisions.", [])],
   ann=[dict(s=1, at=.3, kind="box", line=(4, 5), label="under 5 → free"), dict(s=1, at=2.6, kind="box", line=(6, 7), label="under 18 or student → 100"),
        dict(s=1, at=6.0, kind="box", line=(8, 9), label="everyone else → 200"), dict(s=2, at=2.5, kind="term", text="Ticket price: 100", label="15 → elif was True"),
        dict(s=4, at=2.0, kind="term", text="Ticket price: 200", label="both False → else")],
   zoom=[(0, .4, 1.25, .4, .35), (2, .2, 1.0, .5, .5), (3, 0, 1.3, .35, .2), (4, 0, 1.0, .5, .5)]),
 dict(kind="try", id="try", chapter="Try it", line="Your turn. Store an age, and print can vote if it's eighteen or more, and not yet otherwise. Pause the video, or try it during this timer.",
   task=["Store an age in a variable", "18 or more → print \"Can vote\"", "otherwise → print \"Not yet\""], pause=10.0),
 dict(kind="screen", id="solution", chapter="Try it", beats=[
   ("Here's one solution.", [dict(do="clear"), F("vote.py", S1)]),
   ("With seventeen, it prints, not yet.", [R(.2)]),
   ("Change it to eighteen, and it prints, can vote, because greater than or equal includes eighteen itself.", [E(S2, .8, 6), R(2.0)])],
   ann=[dict(s=2, at=3.5, kind="box", line=(3, 3), cols=(6, 8), label=">= includes 18")], zoom=[(0, .4, 1.25, .4, .3), (1, 1.0, 1.0, .5, .5)]),
 dict(kind="head", id="recap", chapter="Recap", lines=[
   "Let's recap. If runs code only when a condition is true, and else catches everything else.",
   "Elif adds more choices, and Python stops at the first true one, so put the strictest check first.",
   "Indentation decides what belongs to the if. And in conditions, compare with double equals.",
   "If you got stuck anywhere, rewatch that chapter, then change the numbers and predict the output before you run it.",
   "Next time, we'll make code repeat itself with loops. Subscribe so you don't miss it, and I'll see you in the next small step."],
   panel=[(0, "if / else", "#E8590C"), (1, "elif: strictest first", "#2F6DB5"), (2, "indent = belongs to", "#2B8A3E"), (2, "compare with ==", "#C92A2A")]),
]
