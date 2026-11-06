"""Exports intents.yaml as a Dialogflow ES agent ZIP (Dialogflow console -> agent settings -> Export and Import ->
Restore from ZIP). The free Standard edition of Dialogflow ES is enough. Also writes a Botpress-style intents JSON.
    python export_dialogflow.py -> dialogflow-agent.zip, botpress-intents.json"""
import json, uuid, zipfile, yaml
I = yaml.safe_load(open("intents.yaml"))
uid = lambda s: str(uuid.uuid5(uuid.NAMESPACE_URL, "codeinsmallsteps/" + s))
agent = {"description": "Code in Small Steps FAQ bot", "language": "en", "supportedLanguages": [], "defaultTimezone": "Asia/Kolkata", "enableOnePlatformResponses": True,
         "mlMinConfidence": 0.3, "apiVersion": "v2", "isPrivate": True, "webhook": {"url": "", "available": False, "useForDomains": False}}
with zipfile.ZipFile("dialogflow-agent.zip", "w", zipfile.ZIP_DEFLATED) as z:
    z.writestr("agent.json", json.dumps(agent, indent=2)); z.writestr("package.json", json.dumps({"version": "1.0.0"}))
    for name, v in {**I, "Default Fallback Intent": {"examples": [], "responses": ["Sorry, I didn't get that. Ask about price, certificates, setup, schedule, or type 'human'."]}}.items():
        intent = {"id": uid(name), "name": name, "auto": True, "contexts": [], "priority": 500000, "webhookUsed": False, "fallbackIntent": name == "Default Fallback Intent",
                  "events": [{"name": "WELCOME"}] if name == "greeting" else [],
                  "responses": [{"resetContexts": False, "action": name, "affectedContexts": [], "parameters": [], "messages": [{"type": "0", "lang": "en", "condition": "", "speech": v["responses"]}],
                                 "endInteraction": name == "goodbye"}]}
        z.writestr(f"intents/{name}.json", json.dumps(intent, indent=2))
        if v["examples"]:
            z.writestr(f"intents/{name}_usersays_en.json", json.dumps([{"id": uid(name + e), "data": [{"text": e, "userDefined": False}], "isTemplate": False, "count": 0, "updated": 0} for e in v["examples"]], indent=2))
json.dump({"intents": [{"name": k, "utterances": {"en": v["examples"]}, "slots": [], "contexts": ["global"]} for k, v in I.items()]}, open("botpress-intents.json", "w"), indent=1)
print("dialogflow-agent.zip:", len(I), "intents +1 fallback;", sum(len(v["examples"]) for v in I.values()), "training phrases")
