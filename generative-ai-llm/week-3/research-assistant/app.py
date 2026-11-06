"""Gradio interface for the research assistant: enter a topic, watch each agent's step live, read the report, and
download it as Markdown.   python app.py -> http://localhost:7862"""
import os, re, tempfile
import gradio as gr
from agents import research
def run(topic):
    if not topic or len(topic.strip()) < 3: yield "Enter a topic of at least 3 characters.", "", None; return
    steps = []
    def on(node, upd): steps.append(f"✅ **{node.title()}**: {upd['log'][0]['msg'][:300]}")
    yield "⏳ Searcher is planning queries…", "", None
    st = research(topic.strip(), on)
    path = os.path.join(tempfile.gettempdir(), re.sub(r"[^a-z0-9]+", "-", topic.lower()).strip("-")[:50] + ".md"); open(path, "w").write(st["report"])
    yield "\n\n".join(steps) + f"\n\nCitation check: {st['checks']['citations']} citations, invalid: {st['checks']['invalid_citations'] or 'none'}", st["report"], path
with gr.Blocks(title="Research assistant") as demo:
    gr.Markdown("## 🔎 Multi-agent research assistant\nThree agents (Searcher → Summarizer → Writer) research a topic from live sources and write a cited report.")
    with gr.Row():
        topic = gr.Textbox(label="Topic", placeholder="e.g. vector databases in Python", scale=4); go = gr.Button("Research", variant="primary", scale=1)
    gr.Examples(["vector databases in Python", "web scraping libraries", "LLM evaluation frameworks"], topic)
    with gr.Row():
        with gr.Column(scale=1): steps = gr.Markdown(label="Agent steps"); file = gr.File(label="Download report")
        with gr.Column(scale=2): report = gr.Markdown(label="Report")
    go.click(run, topic, [steps, report, file]); topic.submit(run, topic, [steps, report, file])
if __name__ == "__main__": demo.launch(server_name="0.0.0.0", server_port=int(os.environ.get("PORT", 7862)))
