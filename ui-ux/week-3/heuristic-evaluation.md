# Heuristic evaluation: SkillNexis course page (student view)

**Product:** skillnexis.in, signed-in student, course page (`/course/<id>`) and assignment submission.
**Method:** Nielsen's 10 usability heuristics. Severity runs from 0 (not a problem) to 4 (usability catastrophe).
**Evaluator:** one evaluator, a daily user of the page while completing this course.
**Evidence:** what the page shows, plus checks of the live DOM in the browser (labels, roles, link targets).
Observations were made on 4 Nov 2026 and may differ from later versions.

## Findings, by severity

| # | Finding | Where | Heuristic | Severity |
|---|---|---|---|---|
| 1 | After submitting the **last** week, the confirmation reads "Assignment submitted — **Week 4 is now unlocked!**". There is no week 5, and the expected message would point to the quiz or certificate. | Submission box, week 4 | 1. Visibility of system status · 2. Match with the real world | 3 |
| 2 | Clicking a **locked** week (e.g. "Week 4 — Submit Week 3 assignment") switches to an **empty** content area. No message says why it's empty or what to do. The tab is a normal enabled `<button>` with no `aria-disabled`. | Week tabs | 1. Visibility of status · 5. Error prevention | 3 |
| 3 | The assignment link field has **no label**, only placeholder text (`e.g. https://github.com/...`). The placeholder disappears while typing, and screen readers announce an unnamed field. | Submission box | 6. Recognition rather than recall · accessibility (WCAG 1.3.1, 3.3.2) | 3 |
| 4 | Some courses (e.g. Cloud Computing with AWS, weeks 2–4) show only generic tasks: "Watch Week N core concept lectures / Practice coding challenges / Submit code link". There is no topic or deliverable, unlike other courses that list concrete tasks and a mini project. Students can't tell what a complete submission is. | Module description | 2. Match with the real world · 10. Help and documentation | 3 |
| 5 | A mistyped course URL shows only "**Course Not Found…**": no link back to the dashboard, no list of enrolled courses, no search. | `/course/<wrong-id>` | 9. Help users recognise, diagnose and recover from errors | 2 |
| 6 | The **browser tab title** is the same marketing title on every page ("Skill Nexis — Listed on AICTE Internship Portal…"). With several courses open, tabs are indistinguishable, and screen-reader users aren't told which page loaded. | `<title>` | 6. Recognition rather than recall · WCAG 2.4.2 | 2 |
| 7 | One of the two theme-toggle buttons is an **icon with no accessible name** (`<button class="theme-toggle"><i class="fas fa-sun">`). The other one does have a label. The notification counter "9" has no label either. | Header | 4. Consistency and standards · WCAG 4.1.2 | 2 |
| 8 | Week tabs behave as tabs but are plain buttons, with no `role="tab"` or `aria-selected`. The selected week is shown only visually. | Week tabs | 4. Consistency and standards | 1 |
| 9 | Submitted state offers "View submission / Change Link / Remove & Resubmit" but no timestamp of when it was submitted. | Submission box | 1. Visibility of system status | 1 |

**What works well:** progress is clear ("Overall Progress 75%", each week marked Completed / In progress / Locked).
The unlock rule is stated on the locked tab ("Submit Week 3 assignment to unlock"). The download is a real link to a
PDF. Body text contrast in dark mode is high (≈ 9:1, `#B8BEB0` on `#272B25`). The page has `lang="en"` and a
viewport meta, and its images have alt text.

## Recommendations (in priority order)
1. **Fix the final-week message:** "All 4 weeks submitted. Your quiz and certificate are now unlocked." with a button to them. (Finding 1)
2. **Locked weeks:** keep them selectable to preview the syllabus, but show an inline state in the content area.
   For example: "Week 4 opens after you submit week 3. [Go to week 3]". Mark the tab `aria-disabled="true"`. (2, 8)
3. **Label the link field:** add a visible label ("Project link (GitHub, Drive or CodePen)"). Validate the URL
   before enabling Submit, and show an inline error that says what's wrong. (3)
4. **Concrete weekly briefs for every course:** topics, 3–4 tasks and a mini project, as the UI/UX and IoT courses
   already have. Add a "what a complete submission includes" checklist. (4)
5. **Recovery on "Course Not Found":** link to the dashboard and list the enrolled courses. (5)
6. **Per-page titles:** for example "UI/UX Designer — Week 3 · SkillNexis". Add `aria-label`s to icon-only buttons
   and the counter ("9 unread notifications"). (6, 7)
7. Show "Submitted on 4 Nov 2026, 13:02" next to the submission. (9)

## How the findings were checked
| Finding | Check in the live page |
|---|---|
| 1 | Submitted the final week of the IoT with AI course and read the confirmation text |
| 2 | Clicked locked week tabs on two courses: the module area was empty; `button.disabled == false`, `aria-disabled` absent |
| 3 | `input[type=url]`: `labels.length == 0`, no `aria-label`; only `placeholder` set |
| 5 | Opened `/course/aws-cloud` (the real id is `aws`): page text "Course Not Found..." and nothing else in `<main>` |
| 6 | `document.title` identical on the dashboard and on every course page |
| 7 | `button.theme-toggle` has no text and no `aria-label` |
