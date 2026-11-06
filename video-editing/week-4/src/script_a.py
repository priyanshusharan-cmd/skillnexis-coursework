"""Script for the long-form video (video A): "5 money habits that keep hostel friendships alive".
Structure: HOOK (0-15 s) -> promise -> 5 habits (each: presenter says the why, screen shows the how) -> recap -> CTA.
Each scene is a list of shots; each shot owns some narration sentences, so every cut lands on a sentence boundary.
Shot kinds: ("host",) presenter on the café background · ("rec", name, start_s) prototype screen recording ·
("card", title, [lines]) kinetic text · ("chart",) animated spending chart · ("logo",) the week-3 logo reveal."""
TITLE = "5 money habits that keep hostel friendships alive"
SCENES = [
 ("hook", "Cold open", [
   (("host",), ["Last semester, my room almost broke up over two hundred and sixty six rupees.",
                "Not because anyone was cheating.", "Because nobody could remember who paid for the Wi-Fi.", "Three of us were sure we had paid it. The fourth one actually had."]),
   (("card", "Small money. Big fights.", ["₹60 chai", "₹480 cab", "₹799 Wi-Fi", "₹360 Maggi"]), ["Sound familiar?", "Small payments, made by different people, all month long."])], []),
 ("logo", "Intro", [(("logo",), [])], []),
 ("promise", "What you'll learn", [
   (("host",), ["In this video I'll share five habits that fixed it for us.", "They work with any app, or even a notebook.",
                "I'll show each one in Hisaab, an expense splitting app I designed for students, so you can see exactly how it looks."]),
   (("card", "5 habits", ["1  Log it when you pay", "2  Split fairly, not equally", "3  Pick one settle day", "4  Let the app ask", "5  Know where it goes"]),
    ["Here's the list.", "Stick around for habit four. It's the one that saves friendships."])], []),
 ("h1", "Habit 1: Log it when you pay", [
   (("host",), ["Habit one. Log it the moment you pay.", "Not tonight, and not at the end of the month.",
                "Memory is the most expensive part of splitting money. Every expense you add later is one you might get wrong.", "We tested this in our room. Expenses added on the spot were always right. Expenses added at night were wrong about one time in five."]),
   (("rec", "add", 0.8), ["In Hisaab, adding takes about ten seconds.", "Open your room's group, and tap the plus button.",
                          "The amount pad opens first, because the amount is the one thing you always know.",
                          "Paid by defaults to you, and the split defaults to everyone in the group.", "So most of the time, you type a number and hit save."])],
   [("Habit 1", 0, 4), ("Add in ~10 s", 6, 11), ("Smart defaults", 13, 99)]),
 ("h2", "Habit 2: Split fairly, not equally", [
   (("host",), ["Habit two. Split fairly, not equally.", "Equal splits feel simple, but they quietly annoy people.",
                "If Aarav was at the library during the Maggi run, he shouldn't pay for it. And he shouldn't have to argue about it either.", "Fair means everyone pays for what they were part of. That's it."]),
   (("rec", "add", 14.5), ["So the split screen starts with everyone ticked, and you untick whoever wasn't there.",
                           "Hisaab recalculates instantly. A hundred and twenty each, three people.",
                           "And it shows that the total still adds up to three sixty, so nobody has to double check the maths.",
                           "For rent or a trip, you can switch to exact amounts, shares, or percentages."])],
   [("Habit 2", 0, 4), ("Untick who wasn't there", 3, 9), ("₹120 × 3 = ₹360", 10, 99)]),
 ("h3", "Habit 3: Pick one settle day", [
   (("host",), ["Habit three. Pick one settle day.", "Ours is Sunday evening.",
                "When settling is a routine, asking for money stops being personal. It's just Sunday.", "It also keeps the amounts small. Settling ninety rupees every week is easier than five hundred at month end."]),
   (("rec", "settle", 0.8), ["On settle day, open home and tap settle up.", "You see exactly who you're paying, their UPI ID, and what it's for.",
                             "Pick any UPI app and confirm. The money goes bank to bank. Hisaab never holds it.",
                             "Your balance updates straight away, and you can clear the next person in the same sitting."])],
   [("Habit 3", 0, 4), ("Bank to bank via UPI", 5, 12), ("Balance updated", 13, 99)]),
 ("h4", "Habit 4: Let the app ask", [
   (("host",), ["Habit four, the friendship saver. Let the app do the asking.",
                "Nobody wants to be the person sending, hey, about that hundred and twenty.",
                "But a neutral reminder, with the exact amount and a pay link, doesn't feel like nagging.", "The app becomes the bad guy, and you get to stay the friend."]),
   (("rec", "extras", 1.2), ["Tap remind, and pick a tone. Friendly, direct, or funny.",
                             "The message goes from your own WhatsApp, so you decide when it's sent.",
                             "Hisaab never sends automatic reminders behind your back. That was a deliberate design choice."])],
   [("Habit 4", 0, 4), ("You choose the tone", 2, 9), ("Never automatic", 11, 99)]),
 ("h5", "Habit 5: Know where it goes", [
   (("chart",), ["Habit five. Know where the money goes.", "Here's a sample month for one student in our room.",
                 "Food and chai is almost half. Travel is next. Room and bills are smaller than you'd think."]),
   (("rec", "extras", 8.4), ["Hisaab shows this as monthly insights.", "And the most useful part is the nudge at the bottom.",
                             "Late night food was the biggest category, so it suggests a monthly limit. You can take it or ignore it."])],
   [("Habit 5", 0, 4), ("Insights + a gentle nudge", 4, 99)]),
 ("mistakes", "3 mistakes to avoid", [
   (("card", "3 mistakes to avoid", ["Rounding everything up", "One person as the room's bank", "Settling only when someone's broke"]),
    ["Before we wrap up, three mistakes we made, so you don't have to.", "One. Rounding everything up. Ten rupees here and there adds up, and someone always notices.",
     "Two. Letting one person become the room's bank. They end up owed thousands, and too shy to ask.",
     "Three. Settling only when someone is broke. By then the amounts are big, and the conversation is awkward."]),
   (("host",), ["All three have the same fix. Small amounts, logged right away, settled on a fixed day."])], []),
 ("recap", "Recap", [
   (("card", "Recap", ["Log it when you pay", "Split fairly, not equally", "Pick one settle day", "Let the app ask", "Know where it goes"]),
    ["Quick recap.", "Log it when you pay. Split fairly. Settle on one day. Let the app ask. And know where it goes.",
     "None of these are about maths. They're about making money boring, so friendships don't have to absorb it."])], []),
 ("outro", "Thanks for watching", [
   (("host",), ["If this helped, subscribe for more student money tips.", "Next, I'll show how I designed Hisaab in one week, from research to prototype.",
                "Link on screen now. See you there."])], []),
]
