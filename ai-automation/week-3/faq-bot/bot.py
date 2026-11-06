"""FAQ bot: classify -> answer, or fall back when confidence is below the tuned threshold.
    python bot.py            (chat in the terminal)      python bot.py "is it free?"   (one message)"""
import json, os, random, sys, joblib, yaml
HERE = os.path.dirname(os.path.abspath(__file__))
M = joblib.load(os.path.join(HERE, "model.joblib")); I = yaml.safe_load(open(os.path.join(HERE, "intents.yaml"))); TH = json.load(open(os.path.join(HERE, "threshold.json")))["threshold"]
FALLBACK = "Sorry, I'm not sure I understood. I can help with: course price, certificates, installing Python, the lesson schedule, course length, prerequisites and Python errors. Or type 'human' for the support team."
def respond(text):
    p = M.predict_proba([text])[0]; i = p.argmax(); intent, conf = M.classes_[i], float(p[i])
    if conf < TH: return dict(intent="fallback", confidence=round(conf, 2), reply=FALLBACK, guess=intent)
    return dict(intent=intent, confidence=round(conf, 2), reply=random.Random(text).choice(I[intent]["responses"]))
if __name__ == "__main__":
    if len(sys.argv) > 1: print(json.dumps(respond(" ".join(sys.argv[1:])), indent=1)); sys.exit()
    print("FAQ bot (Ctrl+C to quit)")
    while True:
        r = respond(input("you> ")); print(f"bot> {r['reply']}   [{r['intent']} {r['confidence']}]")
