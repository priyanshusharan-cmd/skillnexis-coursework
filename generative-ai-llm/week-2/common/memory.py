"""Conversation memory, three strategies (LangChain message objects; LangChain 1.x dropped its old memory classes,
so these are small explicit implementations):
  BufferMemory   every turn, verbatim                 - most faithful, grows without limit
  WindowMemory   the last k turns verbatim             - bounded, forgets older context completely
  SummaryMemory  a running summary of older turns + the last k verbatim - bounded and keeps the gist
Summaries are written by the LLM when one is configured; otherwise an extractive summary keeps the most informative
sentence of each older turn plus its topic keywords. Every memory can also turn a follow-up ("what about its
syntax?") into a standalone search query using the topics in memory."""
import re
from collections import Counter
from langchain_core.messages import AIMessage, HumanMessage
from .models import chat_model
STOP = set("the a an of to in is are and or for on with what how does do i can be by it its this that as from which when why who about tell me more you your now going back first topic was were".split())
def toks(t): return [w for w in re.findall(r"[a-z0-9_]+", t.lower()) if w not in STOP and len(w) > 2]
def est_tokens(text): return max(1, round(len(text) / 4))                 # ~4 characters per token for English
class BufferMemory:
    name = "buffer"
    def __init__(self): self.msgs = []
    def add(self, q, a): self.msgs += [HumanMessage(q), AIMessage(a)]
    def context(self): return "\n".join(f"{'User' if isinstance(m, HumanMessage) else 'Assistant'}: {m.content}" for m in self.msgs)
    def topics(self, n=4): return [w for w, _ in Counter(w for m in self.msgs if isinstance(m, HumanMessage) for w in toks(m.content)).most_common(n)]
    def earliest(self):
        """Topic words of the oldest question this memory still holds (buffer: the first one; window: only what fits)."""
        first = next((m.content for m in self.msgs if isinstance(m, HumanMessage)), ""); return toks(first)
    def standalone(self, q):
        """Turn a follow-up into a standalone search query. 'Going back to the first topic' uses the oldest topic in
        memory; a pronoun with no new topic word ('which methods does it generate?') uses the previous question."""
        ql = q.lower(); llm = chat_model(); last = next((m.content for m in reversed(self.msgs) if isinstance(m, HumanMessage)), "")
        if llm is not None and self.msgs:
            return llm.invoke(f"Conversation so far:\n{self.context()}\nRewrite the follow-up as a standalone question.\nFollow-up: {q}\nStandalone question:").content.strip()
        if re.search(r"\b(first topic|going back|earlier|at the start|originally)\b", ql): return q + " " + " ".join(self.earliest())
        if re.search(r"\b(it|its|that|this|they|them|those|these)\b", ql) and last: return q + " " + " ".join(toks(last))
        return q
    def size(self): return est_tokens(self.context())
class WindowMemory(BufferMemory):
    name = "window"
    def __init__(self, k=2): super().__init__(); self.k = k
    def add(self, q, a): super().add(q, a); self.msgs = self.msgs[-2 * self.k:]
class SummaryMemory(BufferMemory):
    name = "summary"
    def __init__(self, k=1): super().__init__(); self.k, self.summary = k, ""
    def add(self, q, a):
        super().add(q, a)
        while len(self.msgs) > 2 * self.k:
            old_q, old_a = self.msgs[0].content, self.msgs[1].content; self.msgs = self.msgs[2:]; self.summary = self._fold(self.summary, old_q, old_a)
    def _fold(self, summary, q, a):
        llm = chat_model()
        if llm is not None:
            return llm.invoke(f"Current summary: {summary or '(none)'}\nNew exchange:\nUser: {q}\nAssistant: {a}\nUpdate the summary in at most 3 sentences.").content.strip()
        first = re.split(r"(?<=[.!?])\s+", re.sub(r"\s*\[\d+\]", "", a).strip())[0][:220]
        return (summary + " " if summary else "") + f"User asked about {', '.join(toks(q)[:4])}; answer: {first}"
    def context(self): return (f"Summary of earlier conversation: {self.summary}\n" if self.summary else "") + super().context()
    def earliest(self):
        m = re.search(r"User asked about ([^;]+);", self.summary); return m.group(1).replace(",", " ").split() if m else super().earliest()
