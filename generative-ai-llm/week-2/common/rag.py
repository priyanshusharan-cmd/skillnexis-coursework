"""Shared RAG pieces: a hybrid retriever (Chroma vector search + BM25, merged with reciprocal-rank fusion, at most 2
chunks per document for diversity), an LCEL chain with numbered sources, and an extractive fallback 'generator' used
when no LLM is configured: it picks the sentences that best match the question (embedding + keyword overlap) and
cites them, and abstains when nothing is relevant enough."""
import os, re
import numpy as np, chromadb
from rank_bm25 import BM25Okapi
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda
from .models import chat_model, embeddings
TOK = lambda t: re.findall(r"[a-z0-9_]+", t.lower())
STOP = set("the a an of to in is are and or for on with what how does do i can be by it this that as from which when why who use used using should about you your me my we our".split())
class HybridRetriever:
    def __init__(self, db, collection="peps", emb_path=None, k=5):
        self.col = chromadb.PersistentClient(path=db).get_collection(collection); self.emb = embeddings(emb_path or os.path.join(db, "lsa.pkl")); self.k = k
        got = self.col.get(include=["documents", "metadatas"]); self.ids, self.texts, self.metas = got["ids"], got["documents"], got["metadatas"]
        self.bm25 = BM25Okapi([[w for w in TOK(t) if w not in STOP] for t in self.texts]); self.pos = {i: n for n, i in enumerate(self.ids)}
    def search(self, q, k=None, where=None):
        k = k or self.k; v = self.col.query(query_embeddings=[self.emb.embed_query(q)], n_results=30, where=where)
        vec = v["ids"][0]; bm = np.argsort(-self.bm25.get_scores([w for w in TOK(q) if w not in STOP]))[:30]
        rrf = {}
        for r, i in enumerate(vec): rrf[i] = rrf.get(i, 0) + 1 / (60 + r)
        for r, j in enumerate(bm):
            i = self.ids[j]
            if where and any(self.metas[j].get(a) != b for a, b in where.items()): continue
            rrf[i] = rrf.get(i, 0) + 1 / (60 + r)
        out, per = [], {}
        for i, s in sorted(rrf.items(), key=lambda x: -x[1]):
            n = self.pos[i]; src = self.metas[n]["source"]
            if per.get(src, 0) >= 2: continue
            per[src] = per.get(src, 0) + 1; out.append(Document(page_content=self.texts[n], metadata=dict(self.metas[n], score=round(s, 4))))
            if len(out) == k: break
        return out
def fmt(docs): return "\n\n".join(f"[{i}] ({d.metadata['source']}: {d.metadata.get('title', '')}{', page ' + str(d.metadata['page']) if 'page' in d.metadata else ''})\n{d.page_content}" for i, d in enumerate(docs, 1))
PROMPT = ChatPromptTemplate.from_messages([("system", "Answer using ONLY the numbered sources. Cite like [1]. If the sources don't contain the answer, say you don't know. Be concise."),
                                           ("human", "{history}Question: {question}\n\nSources:\n{context}")])
def extractive(question, docs, emb, n=3, min_rel=0.12):
    """No-LLM answer: best-matching sentences from the retrieved chunks, each with its citation."""
    qv = np.array(emb.embed_query(question)); qt = {w for w in TOK(question) if w not in STOP}; cands = []
    for i, d in enumerate(docs, 1):
        for s in re.split(r"(?<=[.!?])\s+|\n\s*\n", d.page_content):
            s = " ".join(s.split())
            if len(s.split()) < 6 or len(s) > 600 or sum(c.isalpha() for c in s) / len(s) < .6: continue
            cands.append((s, i))
    if not cands: return "I don't know: nothing relevant was retrieved.", []
    E = np.array(emb.embed_documents([c[0] for c in cands])); sem = E @ qv
    lex = np.array([len(qt & set(TOK(c[0]))) / (len(qt) or 1) for c in cands]); score = .6 * sem + .4 * lex
    order = np.argsort(-score)
    if score[order[0]] < min_rel or lex.max() < .3: return "I don't know. The documents don't seem to cover this.", []      # weak match, or fewer than ~1 in 3 of the question's key words appear
    picked, seen = [], set()
    for j in order:
        s, i = cands[j]
        if any(s in x or x in s or len(set(s.split()) & set(x.split())) > .7 * min(len(s.split()), len(x.split())) for x in seen) or score[j] < score[order[0]] * .6: continue
        seen.add(s); picked.append((s, i))
        if len(picked) == n: break
    return " ".join(f"{s} [{i}]" for s, i in picked), sorted({i for _, i in picked})
def answer(retriever, question, history=""):
    docs = retriever.search(question); llm = chat_model()
    if llm is not None:
        chain = PROMPT | llm | StrOutputParser(); text = chain.invoke(dict(question=question, context=fmt(docs), history=history)); used = sorted({int(x) for x in re.findall(r"\[(\d+)\]", text) if int(x) <= len(docs)})
        engine = type(llm).__name__
    else:
        text, used = extractive(question, docs, retriever.emb); engine = "extractive"
    return dict(answer=text, engine=engine, sources=[dict(n=i, source=docs[i - 1].metadata["source"], title=docs[i - 1].metadata.get("title"), url=docs[i - 1].metadata.get("url"),
                                                         page=docs[i - 1].metadata.get("page")) for i in used], retrieved=[d.metadata["source"] for d in docs])
def rag_chain(retriever):
    """The same pipeline as an LCEL Runnable: {"question": ...} -> answer dict."""
    return RunnableLambda(lambda x: answer(retriever, x["question"], x.get("history", "")))
