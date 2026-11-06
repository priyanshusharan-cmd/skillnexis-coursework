"""Knowledge base over PDFs: ingest (pypdf, page by page, keeping file and page number) -> chunk -> embed -> ChromaDB;
ask -> hybrid retrieval -> grounded answer with [n] citations pointing at file + page (LLM when configured,
extractive otherwise). Re-ingesting a file replaces its old chunks, and files are identified by content hash."""
import hashlib, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import chromadb
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from common.models import LSAEmbeddings, embeddings
from common import rag
HERE = os.path.dirname(os.path.abspath(__file__)); DB = os.path.join(HERE, "db"); EMB = os.path.join(DB, "lsa.pkl")
SPLIT = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
def pdf_pages(path):
    r = PdfReader(path); name = os.path.basename(path); title = (r.metadata.title if r.metadata and r.metadata.title else name)
    for i, p in enumerate(r.pages, 1):
        t = (p.extract_text() or "").strip()
        if t: yield Document(page_content=t, metadata=dict(source=name, title=title, page=i))
def ingest(paths, refit=True):
    """Adds PDFs. With the offline LSA embeddings the vocabulary is refitted on the whole library, so every chunk is
    re-embedded (fine for hundreds of PDFs; a hosted embedding model makes ingestion incremental)."""
    os.makedirs(DB, exist_ok=True); client = chromadb.PersistentClient(path=DB); col = client.get_or_create_collection("kb-docs", metadata={"hnsw:space": "cosine"})
    old = col.get(include=["documents", "metadatas"]); keep = {}
    for i, d, m in zip(old["ids"], old["documents"], old["metadatas"]): keep[i] = (d, m)
    added, bad = [], []
    for p in paths:
        try: pages = list(pdf_pages(p))
        except Exception as e: bad.append((os.path.basename(p), str(e))); continue
        if not pages: bad.append((os.path.basename(p), "no text layer (scanned? needs OCR)")); continue
        h = hashlib.sha1(open(p, "rb").read()).hexdigest()[:10]; name = os.path.basename(p)
        keep = {k: v for k, v in keep.items() if v[1]["source"] != name}
        for j, c in enumerate(SPLIT.split_documents(pages)): keep[f"{h}-{j}"] = (c.page_content, dict(c.metadata, sha=h))
        added.append(name)
    client.delete_collection("kb-docs"); col = client.create_collection("kb-docs", metadata={"hnsw:space": "cosine"})
    ids = list(keep); texts = [keep[i][0] for i in ids]; metas = [keep[i][1] for i in ids]
    emb = embeddings(EMB)
    if isinstance(emb, LSAEmbeddings): emb = LSAEmbeddings(dim=min(256, max(16, len(texts) // 3)), path=EMB).fit(texts)
    vec = emb.embed_documents(texts)
    for k in range(0, len(ids), 500): col.add(ids=ids[k:k + 500], documents=texts[k:k + 500], embeddings=vec[k:k + 500], metadatas=metas[k:k + 500])
    return dict(added=added, failed=bad, chunks=len(ids), files=sorted({m["source"] for m in metas}))
def retriever(): return rag.HybridRetriever(DB, collection="kb-docs", emb_path=EMB, k=5)
def ask(question, history="", R=None):
    return rag.answer(R or retriever(), question, history)
if __name__ == "__main__":
    import glob, json; print(json.dumps(ingest(sorted(glob.glob(os.path.join(HERE, "pdfs", "*.pdf")))), indent=1))
