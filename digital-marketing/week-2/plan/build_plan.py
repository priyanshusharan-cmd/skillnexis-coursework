"""Builds the 2-week content calendar (CSV + Markdown) and the engagement tracker (Excel with formulas).
    python plan/build_plan.py
"""
import csv, os
from datetime import date, timedelta
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.formatting.rule import CellIsRule

HERE = os.path.dirname(os.path.abspath(__file__))
START = date(2026, 11, 10)   # Monday, campaign day 1
TAGS = "#StudyFuel #BengaluruCafe #StudentLife #ExamSeason #BLRFood"
# day, time, format, asset, pillar, caption, alt text, CTA, goal metric
ROWS = [
 (0, "11:00", "Feed", "01-launch", "Launch", "Exam season? We saved you a corner. 📚 Quiet tables, fast Wi-Fi and refills that keep up with your syllabus. Study Fuel runs 10–23 Nov.", "Illustrated coffee cup on a cream background with the headline 'Exam season? We saved you a corner.'", "Save + share with your study group", "Reach, saves"),
 (0, "19:30", "Story", "13-story-countdown", "Launch", "Study Fuel starts today, 3 pm. Tap remind me.", "Countdown sticker to the Study Fuel launch", "Countdown reminder", "Reminder taps"),
 (1, "13:00", "Feed", "02-offer", "Offer", "₹149 Study Fuel combo: filter coffee or masala chai + banana-walnut bread. Weekdays 3–7 pm, show your college ID.", "Dark brown poster with ₹149 Study Fuel combo, crossed-out ₹210", "Visit 3–7 pm", "Profile visits, direction taps"),
 (1, "20:00", "Story", "12-story-poll", "Engagement", "Late-night revision needs… coffee or chai?", "Poll: coffee vs chai", "Vote", "Poll votes"),
 (2, "18:00", "Reel", "09-reel-latte", "Behind the scenes", "60 seconds of latte art to reset your brain between chapters. 🎨☕", "Reel cover: play button and '60-second latte art'", "Watch + share", "Plays, shares"),
 (3, "13:00", "Carousel", "06a-carousel-spots", "Value", "4 study spots inside Bean & Bloom. Which one is yours? Swipe →", "Carousel of four study spots: window bar, quiet loft, big table, garden nook", "Comment your spot number", "Saves, comments"),
 (3, "21:00", "Story", "14-story-quiz", "Engagement", "All-nighter or sleep by 12? (Science has an answer.)", "Quiz sticker with three options", "Answer the quiz", "Quiz answers"),
 (4, "17:00", "Feed", "03-tip", "Value", "Study tip #1: the Bean & Bloom Pomodoro. 25 minutes of focus, 5 to refill. Save it for exam week.", "Two cards: 25 minutes of focus, 5 minutes to refill", "Save", "Saves"),
 (5, "11:00", "Feed", "05-ugc", "Community", "Show us your study corner. Tag us with #StudyFuelCorner; every Friday 3 setups win a free combo. We only repost with permission.", "Pink poster: 'Show us your study corner' and #StudyFuelCorner", "Post + tag", "UGC posts, tags"),
 (5, "19:00", "Story", "15-story-visit", "Visit", "Open 8 am–11 pm through exams. 2 min from the main gate.", "Opening hours card with location sticker", "Location sticker tap", "Sticker taps"),
 (6, "12:00", "Reel", "10-reel-order", "Behind the scenes", "What our barista orders in exam week (it's not what you think).", "Reel cover: 'What our barista orders in exam week'", "Comment your order", "Plays, comments"),
 (7, "13:00", "Carousel", "07a-carousel-menu", "Offer", "Everything under ₹150. Student budget, proper food. Swipe for the full list →", "Carousel: menu items and prices under ₹150", "Save for later", "Saves"),
 (7, "20:00", "Story", "12-story-poll", "Engagement", "Week 2 starts! What do you study best with: silence or lo-fi? (re-use poll template)", "Poll sticker", "Vote", "Poll votes"),
 (8, "17:00", "Feed", "04-amenities", "Value", "Built for long study days: 100 Mbps Wi-Fi, a plug at every seat, a quiet loft, free refills.", "Checklist of amenities with a green cup", "Visit", "Profile visits"),
 (9, "13:00", "Carousel", "08a-carousel-streak", "Loyalty", "New: the Study Streak card. Study with us 5 days, the 6th coffee is on us. Valid till 23 Nov.", "Carousel explaining the loyalty card with five stamps and a free drink", "Ask at the counter", "Saves, card sign-ups (counted in store)"),
 (10, "18:00", "Reel", "11-reel-dayin", "Behind the scenes", "A day in the quiet loft, 8 am to 11 pm, in 30 seconds.", "Reel cover: 'A day in the quiet loft'", "Share with a study buddy", "Plays, shares"),
 (11, "17:00", "Feed", "UGC repost", "Community", "This week's #StudyFuelCorner picks (reposted with permission). Winners, DM us to claim your combo!", "Grid of three reposted study setups (from consenting customers)", "Post + tag", "UGC posts"),
 (12, "11:00", "Story", "15-story-visit", "Visit", "Weekend hours: still 8 am–11 pm. The big table is free before noon.", "Hours card", "Location sticker tap", "Sticker taps"),
 (13, "19:00", "Feed", "02-offer", "Offer", "Last day of Study Fuel tomorrow. Good luck for exams, from all of us at Bean & Bloom. 💛", "Study Fuel offer poster (last chance)", "Visit before 23 Nov", "Profile visits, redemptions"),
]
os.makedirs(HERE, exist_ok=True)
with open(os.path.join(HERE, "content-calendar-2wk.csv"), "w", newline="") as f:
    w = csv.writer(f); w.writerow(["Date", "Day", "Time", "Format", "Asset", "Pillar", "Caption", "Hashtags", "Alt text", "CTA", "Success metric"])
    for d, t, fm, a, p, c, alt, cta, m in ROWS:
        dt = START + timedelta(days=d); w.writerow([dt.isoformat(), dt.strftime("%a"), t, fm, a, p, c, TAGS if fm != "Story" else "", alt, cta, m])
md = ["| Date | Time | Format | Asset | Pillar | Caption (short) | CTA |", "|---|---|---|---|---|---|---|"]
for d, t, fm, a, p, c, alt, cta, m in ROWS:
    dt = START + timedelta(days=d); md.append(f"| {dt.strftime('%a %d %b')} | {t} | {fm} | `{a}` | {p} | {c[:80]}{'…' if len(c) > 80 else ''} | {cta} |")
open(os.path.join(HERE, "content-calendar-2wk.md"), "w").write("# 2-week content calendar · Study Fuel (10–23 Nov 2026)\n\nFull captions, hashtags and alt text: [content-calendar-2wk.csv](content-calendar-2wk.csv). Posting times follow the audience: students are most active over lunch (1 pm) and evenings (6–9 pm).\n\n" + "\n".join(md) + "\n")

# ---------- engagement tracker
wb = Workbook(); ws = wb.active; ws.title = "Post tracker"
H = ["Date", "Asset", "Format", "Reach", "Impressions", "Likes", "Comments", "Shares", "Saves", "Profile visits", "Link/sticker taps", "Engagement rate (reach)", "Save rate", "Notes"]
ws.append(H)
for d, t, fm, a, p, c, alt, cta, m in ROWS:
    ws.append([START + timedelta(days=d), a, fm] + [None] * 8 + [None, None, ""])
n = len(ROWS) + 1
for r in range(2, n + 1):
    ws[f"L{r}"] = f'=IF(D{r}>0,(F{r}+G{r}+H{r}+I{r})/D{r},"")'; ws[f"M{r}"] = f'=IF(D{r}>0,I{r}/D{r},"")'
    ws[f"A{r}"].number_format = "dd mmm"; ws[f"L{r}"].number_format = ws[f"M{r}"].number_format = "0.0%"
blue = Font(color="0000FF")
for row in ws.iter_rows(min_row=2, max_row=n, min_col=4, max_col=11):
    for c in row: c.font = blue
hdr = PatternFill("solid", fgColor="3B2416")
for c in ws[1]: c.font = Font(bold=True, color="FFFFFF"); c.fill = hdr; c.alignment = Alignment(wrap_text=True, vertical="center")
for col, wd in zip("ABCDEFGHIJKLMN", (10, 22, 10, 9, 11, 8, 10, 8, 8, 9, 11, 14, 10, 30)): ws.column_dimensions[col].width = wd
ws.freeze_panes = "B2"
ws.conditional_formatting.add(f"L2:L{n}", CellIsRule(operator="greaterThanOrEqual", formula=["Targets!$B$3"], fill=PatternFill("solid", fgColor="DCFAE6")))
s = wb.create_sheet("Summary")
s.append(["Metric", "Total / average", "How it's calculated"])
rows = [("Posts published", f"=COUNTA('Post tracker'!D2:D{n})", "Rows with reach entered"),
        ("Total reach", f"=SUM('Post tracker'!D2:D{n})", "Sum of reach"),
        ("Avg engagement rate", f"=IFERROR(AVERAGE('Post tracker'!L2:L{n}),\"\")", "(likes+comments+shares+saves)/reach, averaged"),
        ("Avg save rate", f"=IFERROR(AVERAGE('Post tracker'!M2:M{n}),\"\")", "Saves/reach: best signal for useful content"),
        ("Profile visits", f"=SUM('Post tracker'!J2:J{n})", "Leads to follows and directions"),
        ("Followers gained", "=Followers!C16-Followers!C2", "From the daily follower log"),
        ("Combo redemptions (in store)", "=SUM(Offline!B2:B15)", "Counted at the till"),
        ("Cost per redemption (₹)", "=IFERROR(Targets!B6/B8,\"\")", "Campaign spend / redemptions")]
for r in rows: s.append(list(r))
for c in ("B4", "B5"): s[c].number_format = "0.0%"
for c in s[1]: c.font = Font(bold=True, color="FFFFFF"); c.fill = hdr
s.column_dimensions["A"].width = 28; s.column_dimensions["B"].width = 16; s.column_dimensions["C"].width = 48
t = wb.create_sheet("Targets")
for r in [("Target", "Value", "Source / reasoning"), ("Followers gained in 2 weeks", 50, "Course requirement (50+)"), ("Engagement rate per post", 0.04, "Assumption: small local accounts often see 3–6 %; replace with the page's own baseline after week 1"),
          ("Save rate on value posts", 0.02, "Assumption, to be validated"), ("Combo redemptions", 150, "≈ 10 per weekday, 3–7 pm"), ("Campaign spend (₹)", 3000, "Printed counter cards + 15 free combos for UGC winners; no paid ads")]:
    t.append(list(r))
for c in ("B3", "B4"): t[c].number_format = "0%"
for row in t.iter_rows(min_row=2, min_col=2, max_col=2):
    for c in row: c.font = blue
for c in t[1]: c.font = Font(bold=True, color="FFFFFF"); c.fill = hdr
t.column_dimensions["A"].width = 30; t.column_dimensions["C"].width = 70
fl = wb.create_sheet("Followers"); fl.append(["Date", "Day", "Followers (enter daily)", "Change", "What we did that day"])
for i in range(15):
    dt = START + timedelta(days=i - 1); r = i + 2
    fl.append([dt, dt.strftime("%a"), None, f'=IF(AND(C{r}<>"",C{r-1}<>""),C{r}-C{r-1},"")' if i else "", "Baseline (day before launch)" if i == 0 else ""])
    fl[f"A{r}"].number_format = "dd mmm"; fl[f"C{r}"].font = blue
for c in fl[1]: c.font = Font(bold=True, color="FFFFFF"); c.fill = hdr
fl.column_dimensions["C"].width = 22; fl.column_dimensions["E"].width = 44
of = wb.create_sheet("Offline"); of.append(["Date", "Study Fuel combos sold", "Study Streak cards issued", "Asked 'how did you hear about us?': Instagram"])
for i in range(14):
    dt = START + timedelta(days=i); of.append([dt]); of[f"A{i + 2}"].number_format = "dd mmm"
for c in of[1]: c.font = Font(bold=True, color="FFFFFF"); c.fill = hdr
for col in "BCD": of.column_dimensions[col].width = 26
wb.save(os.path.join(HERE, "engagement-tracker.xlsx")); print("ok", len(ROWS), "calendar rows")
