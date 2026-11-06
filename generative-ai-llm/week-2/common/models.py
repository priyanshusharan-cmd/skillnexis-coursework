"""Model access for the GenAI weeks, all free.
* chat_model(): a LangChain chat model if one is configured, else None (callers then use the extractive fallback)
    GEMINI_API_KEY  -> langchain_google_genai.ChatGoogleGenerativeAI (free tier)
    OLLAMA_MODEL    -> langchain_ollama.ChatOllama (local, e.g. qwen2.5:1.5b)
    OPENAI_API_KEY  -> langchain_openai.ChatOpenAI (OPENAI_BASE_URL works for Groq/OpenRouter free tiers)
* LSAEmbeddings: a LangChain Embeddings implementation that runs fully offline: TF-IDF (word 1-2 grams) reduced to
  256 dimensions with truncated SVD (latent semantic analysis), L2-normalised. It captures topical similarity
  (synonyms that co-occur), not deep semantics; GEMINI_API_KEY switches to Google's text-embedding-004."""
import os, pickle
import numpy as np
from langchain_core.embeddings import Embeddings
def _env():
    for p in (".env", os.path.join(os.path.dirname(__file__), "..", ".env")):
        if os.path.exists(p):
            for l in open(p):
                if "=" in l and not l.startswith("#"): k, v = l.strip().split("=", 1); os.environ.setdefault(k, v)
_env()
def chat_model(temperature=0.2):
    if os.environ.get("GEMINI_API_KEY"):
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(model=os.environ.get("GEMINI_MODEL", "gemini-2.0-flash"), google_api_key=os.environ["GEMINI_API_KEY"], temperature=temperature)
    if os.environ.get("OLLAMA_MODEL"):
        from langchain_ollama import ChatOllama
        return ChatOllama(model=os.environ["OLLAMA_MODEL"], temperature=temperature)
    if os.environ.get("OPENAI_API_KEY"):
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"), base_url=os.environ.get("OPENAI_BASE_URL"), temperature=temperature)
    return None
def engine_name():
    m = chat_model(); return "extractive (no LLM configured)" if m is None else type(m).__name__
class LSAEmbeddings(Embeddings):
    def __init__(self, dim=256, path=None): self.dim, self.path, self.vec, self.svd = dim, path, None, None
    def fit(self, texts):
        from sklearn.decomposition import TruncatedSVD
        from sklearn.feature_extraction.text import TfidfVectorizer
        self.vec = TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_df=.6, sublinear_tf=True, stop_words="english").fit(texts)
        self.svd = TruncatedSVD(self.dim, random_state=0).fit(self.vec.transform(texts))
        if self.path: pickle.dump((self.vec, self.svd), open(self.path, "wb"))
        return self
    def load(self):
        self.vec, self.svd = pickle.load(open(self.path, "rb")); return self
    def _e(self, texts):
        z = self.svd.transform(self.vec.transform(texts)); z /= np.linalg.norm(z, axis=1, keepdims=True) + 1e-9; return z.tolist()
    def embed_documents(self, texts): return self._e(texts)
    def embed_query(self, text): return self._e([text])[0]
def embeddings(path):
    if os.environ.get("GEMINI_API_KEY"):
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        return GoogleGenerativeAIEmbeddings(model="models/text-embedding-004", google_api_key=os.environ["GEMINI_API_KEY"])
    e = LSAEmbeddings(path=path); return e.load() if os.path.exists(path) else e
