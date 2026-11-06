"""Task 1: vector database. 66 Python Enhancement Proposals (public domain / CC0; 254k words) are split into
overlapping chunks and indexed in a persistent ChromaDB collection with metadata (PEP number, title, status, type, URL).
    python index.py -> chroma/ (persistent DB), results/index.json"""
import json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import chromadb
from langchain_text_splitters import RecursiveCharacterTextSplitter
from common.loaders import load_peps
from common.models import embeddings
HERE = os.path.dirname(os.path.abspath(__file__)); DB = os.path.join(HERE, "chroma"); EMB = os.path.join(HERE, "chroma", "lsa.pkl")
def build():
    docs = load_peps(os.path.join(HERE, "data", "peps")); t = time.time()
    chunks = RecursiveCharacterTextSplitter(chunk_size=1200, chunk_overlap=200, separators=["\n\n", "\n", ". ", " "]).split_documents(docs)
    for i, c in enumerate(chunks): c.metadata["chunk"] = i
    os.makedirs(DB, exist_ok=True); emb = embeddings(EMB)
    if hasattr(emb, "fit") and emb.vec is None: emb.fit([c.page_content for c in chunks])
    client = chromadb.PersistentClient(path=DB)
    try: client.delete_collection("peps")
    except Exception: pass
    col = client.create_collection("peps", metadata={"hnsw:space": "cosine"})
    vecs = emb.embed_documents([c.page_content for c in chunks])
    for k in range(0, len(chunks), 500):
        col.add(ids=[f"c{i}" for i in range(k, min(k + 500, len(chunks)))], documents=[c.page_content for c in chunks[k:k + 500]], embeddings=vecs[k:k + 500], metadatas=[c.metadata for c in chunks[k:k + 500]])
    stats = dict(documents=len(docs), words=sum(len(d.page_content.split()) for d in docs), chunks=col.count(), chunk_size=1200, overlap=200, embedding=type(emb).__name__, dim=len(vecs[0]), seconds=round(time.time() - t, 1))
    json.dump(stats, open(os.path.join(HERE, "results", "index.json"), "w"), indent=1); return stats
if __name__ == "__main__": print(build())
