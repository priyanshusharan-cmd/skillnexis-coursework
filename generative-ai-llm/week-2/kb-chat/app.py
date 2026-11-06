"""Chat with your PDFs (Gradio). Upload PDFs -> they're indexed; ask questions -> grounded answers that cite the file
and page, with the retrieved passages shown alongside. Remembers the conversation (summary memory) for follow-ups.
    python app.py   -> http://localhost:7860"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import gradio as gr
import kb
from common.memory import SummaryMemory
from common.models import engine_name
STATE = dict(R=None)
def R():
    if STATE["R"] is None and os.path.exists(kb.DB): STATE["R"] = kb.retriever()
    return STATE["R"]
def upload(files):
    if not files: return "No files."
    res = kb.ingest([f if isinstance(f, str) else f.name for f in files]); STATE["R"] = None
    return f"Indexed {len(res['added'])} file(s); library: {len(res['files'])} files, {res['chunks']} chunks." + (f" Failed: {res['failed']}" if res["failed"] else "")
def chat(message, history, mem_state):
    if R() is None: yield "Upload some PDFs first.", mem_state, ""; return
    mem = mem_state or SummaryMemory(k=2); q = mem.standalone(message); r = kb.ask(q, history=mem.context(), R=R())
    src = "\n".join(f"[{s['n']}] {s['source']}, page {s['page']}" for s in r["sources"]) or "no sources cited"
    passages = "\n\n".join(f"**{d.metadata['source']} p.{d.metadata['page']}**: {d.page_content[:400]}…" for d in R().search(q, k=3))
    out = ""
    for w in (r["answer"] + "\n\n" + "Sources:\n" + src).split(" "):          # stream word by word
        out += w + " "; time.sleep(.01); yield out, mem, passages
    mem.add(message, r["answer"])
with gr.Blocks(title="PDF knowledge base") as demo:
    gr.Markdown(f"## 📚 Chat with your PDFs\nAnswers come only from your documents, with file and page citations. Engine: **{engine_name()}**.")
    mem = gr.State(None)
    with gr.Row():
        with gr.Column(scale=1):
            files = gr.File(file_count="multiple", file_types=[".pdf"], label="Add PDFs"); status = gr.Markdown(); files.upload(upload, files, status)
            passages = gr.Markdown(label="Retrieved passages")
        with gr.Column(scale=2):
            gr.ChatInterface(chat, additional_inputs=[mem], additional_outputs=[mem, passages], examples=[["What does ParamSpec let you annotate?", None], ["How do I write a union type with the | operator?", None]])
if __name__ == "__main__": demo.launch(server_name="0.0.0.0", server_port=int(os.environ.get("PORT", 7860)))
