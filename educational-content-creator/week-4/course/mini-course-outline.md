# Python in 5 Small Steps: a free mini course

**For:** complete beginners (students and career switchers) who can spare 30 minutes a day for a week.
**Format:** 5 lessons. Each one is a 5-minute video, a one-page cheat sheet, a practice task with a worked solution, and
a 3-question self-check.
**Outcome:** by lesson 5 the learner has written, debugged and explained a small grade-report program from scratch.
**Prerequisites:** none. Python 3.12+ installed, or a free online editor such as
[python.org/shell](https://www.python.org/shell/).
**Delivery:** a YouTube playlist ("Python from zero") plus this outline as a Notion or Google Docs page. Import this
Markdown file directly: Notion via *Import → Markdown*, Google Docs via *File → Open*.

| # | Lesson | Video | Status |
|---|---|---|---|
| 1 | Variables: labelled boxes for values | `upload/01-python-variables.mp4` (5:03 + end screen) | ✅ produced |
| 2 | If / else: let your program choose | `upload/03-python-if-else.mp4` (5:04 + end screen) | ✅ produced |
| 3 | Loops: repeat a task with a rule | script ready (week 1, script 3) | 📝 scripted |
| 4 | Functions: give one job a name | outline below | 🗂 outlined |
| 5 | Mini project: grade report + reading errors | uses `upload/02-read-python-errors.mp4` (3:04) | ◑ part produced |

---

## Lesson 1 · Variables: labelled boxes for values
**Description:** Why can Python add 5 and 2 but join "5" and "2" into "52"? Learners meet variables as labelled boxes,
the three basic types (`int`, `float`, `str`), and see that the *type* decides what `+` does. It ends with the most
common beginner error, a misspelt name.

* **You will be able to:**
  * create and reassign variables;
  * check a value's type with `type()`;
  * convert between types with `int()`, `str()` and `float()`;
  * read a `NameError`.
* **Practice:** store two numbers, add them, and print the result inside a sentence (`print("Total:", total)`).
* **Self-check:**
  1. What does `"3" * 2` print?
  2. Why does `"Age: " + 19` fail?
  3. Is `total score` a valid name?
* **Common mistake:** `input()` always returns a `str`, so convert it before doing maths.

## Lesson 2 · If / else: let your program choose
**Description:** One program, different answers. Learners build a grade checker with `if`, `elif` and `else`, learn
why the *order* of `elif` matters (95 marks printing a C), and fix the two classic errors: `IndentationError` and
`=` vs `==`. They then combine conditions with `and` / `or`.

* **You will be able to:**
  * write branches;
  * use the comparison operators;
  * test boundary values (49, 50, 90);
  * order conditions from strictest to loosest.
* **Practice:** print "Can vote" for ages of 18 or more, otherwise "Not yet". Then add a ticket price: children under
  12 or seniors 60 and over pay ₹50, everyone else ₹100.
* **Self-check:**
  1. What's the difference between `=` and `==`?
  2. Why must `>= 90` come before `>= 75`?
  3. What does `and` need to be true?

## Lesson 3 · Loops: repeat a task with a rule
**Description:** Would you write the same print statement 100 times? Learners trace `for i in range(1, 6)` step by
step, then change the start, stop and step. They meet `while` with a counter, and see why a missing update creates an
infinite loop (and how to stop one with Ctrl+C).

* **You will be able to:**
  * loop over a range and over a list;
  * accumulate a total;
  * choose between `for` (known count) and `while` (until a condition changes).
* **Practice:** print 2, 4, 6, 8, 10, then sum the list `[72, 85, 90]` with a loop and compare the result with
  `sum()`.
* **Self-check:**
  1. What does `range(5)` start at?
  2. What's printed by `for c in "hi": print(c)`?
  3. What makes a `while` loop stop?

## Lesson 4 · Functions: give one job a name
**Description:** Copy-pasted code is a bug factory. Learners wrap the grade logic from lesson 2 in
`def grade(mark):`, see the difference between `return` and `print`, and pass different arguments to reuse it. It
finishes by refactoring a 20-line script into three small functions.

* **You will be able to:**
  * define a function;
  * pass parameters;
  * return a value;
  * explain scope at a beginner level (variables inside a function stay inside).
* **Practice:** write `average(scores)` that returns the mean of a list, and guard it against an empty list.
* **Self-check:**
  1. What does a function without `return` give back?
  2. Why does `print(grade(80))` show the grade but `grade(80)` alone shows nothing in a script?
  3. What's a parameter?

## Lesson 5 · Mini project: a grade report (and reading errors)
**Description:** Everything together. Learners build `report.py`:
* a list of student names and marks;
* a loop that calls `grade()` for each student;
* a class average, guarded against an empty list;
* a neat printed report.

Along the way they hit and fix three real errors (`NameError`, `TypeError`, `ZeroDivisionError`) using the bottom-up
method from the error-reading video.

* **You will be able to:**
  * plan a small program as steps;
  * combine variables, conditions, loops and functions;
  * read any traceback bottom-up.
* **Deliverable:** the finished `report.py`, shared as a GitHub gist or repository, with one change of your own (for
  example a top-scorer line).
* **Self-check:** explain each line of your report to a friend in one sentence.

---

## Course design notes
* **One idea per lesson:** each lesson introduces exactly one concept and reuses the previous ones, a spiral recap.
* **Real output:** every code example runs, and the output on screen is the genuine output.
* **Accessibility:** captions on every video. Code is shown at a minimum of 28 px on a 1080p frame, and ligatures are
  turned off so `>=` looks the way learners type it.
* **Assessment:** practice tasks have worked solutions in the video. Self-checks are answered at the start of the next
  lesson.
* **Measuring success:** completion rate per lesson, practice attempts reported in the comments, and the drop-off
  between lessons in the playlist (YouTube Analytics → *Playlist* report).
