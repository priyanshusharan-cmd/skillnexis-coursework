"""Three responsive, table-based HTML email templates (work in Gmail, Outlook and Apple Mail): welcome, promotional, re-engagement.
    python email/build_emails.py   -> email/*.html (then rendered to exports/email-*.png)
"""
import os
HERE = os.path.dirname(os.path.abspath(__file__))

def email(preheader, eyebrow, title, body_html, cta, cta_note, accent="#3B2416", hero_bg="#FBE3E5"):
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="light only">
<title>{title}</title><style>@media (max-width:600px){{.w{{width:100%!important}}.p{{padding:24px!important}}h1{{font-size:28px!important}}}}</style></head>
<body style="margin:0;background:#F2EBE1;font-family:Inter,Arial,sans-serif;color:#3B2416">
<div style="display:none;max-height:0;overflow:hidden">{preheader}</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#F2EBE1"><tr><td align="center" style="padding:24px 12px">
<table role="presentation" class="w" width="600" cellpadding="0" cellspacing="0" style="background:#FFF7EC;border-radius:16px;overflow:hidden">
<tr><td style="padding:24px 40px;font:800 18px Inter,Arial,sans-serif">☕ Bean &amp; Bloom</td></tr>
<tr><td class="p" style="background:{hero_bg};padding:40px">
  <div style="font:700 12px Inter,Arial;letter-spacing:.14em;text-transform:uppercase;color:#4E6B4A">{eyebrow}</div>
  <h1 style="font:800 34px/1.15 Inter,Arial,sans-serif;margin:12px 0 0">{title}</h1></td></tr>
<tr><td class="p" style="padding:32px 40px;font:400 16px/1.6 Inter,Arial,sans-serif;color:#3B2416">{body_html}
  <table role="presentation" cellpadding="0" cellspacing="0" style="margin:28px 0 8px"><tr><td style="background:{accent};border-radius:10px">
  <a href="https://example.com/beanandbloom" style="display:inline-block;padding:14px 28px;font:700 16px Inter,Arial;color:#FFF7EC;text-decoration:none">{cta}</a></td></tr></table>
  <div style="font-size:13px;color:#6B5444">{cta_note}</div></td></tr>
<tr><td style="padding:24px 40px;border-top:1px solid #EADFD2;font:400 12px/1.6 Inter,Arial;color:#6B5444">
  Bean &amp; Bloom (fictional café for a course project) · near the college main gate, Bengaluru · Open 8 am–11 pm<br>
  You're getting this because you joined our list at the counter or on Instagram. <a href="https://example.com/unsubscribe" style="color:#6B5444">Unsubscribe</a> · <a href="https://example.com/prefs" style="color:#6B5444">Email preferences</a></td></tr>
</table></td></tr></table></body></html>"""

T = {
 "welcome": email("Your first coffee is on us. Here's what else to know.", "Welcome", "Welcome to Bean &amp; Bloom, {{first_name}} 🌱",
   "<p style='margin:0 0 14px'>Thanks for joining. We're a small café two minutes from campus, built for people who need a good table, fast Wi-Fi and a refill that doesn't ruin the budget.</p>"
   "<p style='margin:0 0 6px'><b>What you get as a member</b></p><ul style='margin:0;padding-left:20px'><li>A free filter coffee or chai on your first visit (code below)</li><li>Student offers first, before Instagram</li><li>One email a week at most, with no spam</li></ul>"
   "<p style='margin:18px 0 0;font:800 22px Inter,Arial;letter-spacing:.1em;background:#E3EBDD;display:inline-block;padding:10px 18px;border-radius:8px'>HELLO-{{code}}</p>",
   "Find us on Maps", "Show the code at the counter. Valid 14 days, one per person."),
 "promotional": email("₹149 coffee + banana bread, weekdays 3–7 pm. Exams just got easier.", "Study Fuel · 10–23 Nov", "Exam season? We saved you a corner.",
   "<p style='margin:0 0 14px'>For the next two weeks, the <b>Study Fuel combo</b> is just <b>₹149</b> (usually ₹210): filter coffee or masala chai plus our banana-walnut bread.</p>"
   "<table role='presentation' width='100%' cellpadding='0' cellspacing='0' style='background:#E3EBDD;border-radius:12px'><tr><td style='padding:16px 20px;font-size:15px'>⏰ Weekdays, 3–7 pm<br>🎓 Show your college ID<br>📶 100 Mbps Wi-Fi and a plug at every seat<br>🤫 Quiet loft upstairs, no calls</td></tr></table>"
   "<p style='margin:16px 0 0'>Plus the new <b>Study Streak card</b>: study with us 5 days and the 6th coffee is free.</p>",
   "Plan your study session", "Offer ends 23 Nov. Dine-in only; not valid with other offers.", "#4E6B4A", "#FFF7EC"),
 "reengagement": email("It's been a while. Here's a free brownie to say hi.", "We miss you", "Your table's been missing you, {{first_name}}",
   "<p style='margin:0 0 14px'>It's been about two months since your last visit. A few things changed while you were away:</p>"
   "<ul style='margin:0;padding-left:20px'><li>A new quiet loft upstairs (no calls, no music)</li><li>Hours extended to 11 pm</li><li>Everything on the menu under ₹150</li></ul>"
   "<p style='margin:16px 0 0'>Come back this week and the <b>brownie is on us</b> with any drink. Just show this email.</p>"
   "<p style='margin:16px 0 0;font-size:14px;color:#6B5444'>Not interested any more? No hard feelings: <a href='https://example.com/unsubscribe' style='color:#6B5444'>unsubscribe in one click</a>, and we'll stop emailing.</p>",
   "Claim your free brownie", "Valid for 7 days from this email.", "#B9692B", "#F4E3CF"),
}
for k, v in T.items():
    open(os.path.join(HERE, f"{k}.html"), "w").write(v)
print("ok")
