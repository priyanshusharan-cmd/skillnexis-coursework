"""Mini project: creative text generation with a character-level LSTM (Streamlit).
Pick a model (Shakespeare or Python code), type a seed prompt, and set temperature, top-k and length.
    streamlit run app/streamlit_app.py"""
import os, sys, time
import streamlit as st
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from charlstm import load, sample
MODELS = {"Python code (CPython standard library)": "results/charlstm_python.pt", "Shakespeare": "results/charlstm_shakespeare.pt"}
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
st.set_page_config(page_title="LSTM text generator", page_icon="✍️", layout="wide")
@st.cache_resource
def get(path): return load(os.path.join(ROOT, path))
st.title("✍️ LSTM text generator"); st.caption("A 2-layer character-level LSTM, trained from scratch on a CPU. It learns spelling, syntax and style one character at a time.")
with st.sidebar:
    name = st.selectbox("Model", list(MODELS)); m, ck = get(MODELS[name])
    temp = st.slider("Temperature", .1, 1.6, .7, .05, help="Low = safe and repetitive, high = creative and chaotic")
    topk = st.slider("Top-k (0 = off)", 0, 40, 0); n = st.slider("Max length (characters)", 50, 2000, 500, 50); seed = st.number_input("Random seed", 0, 9999, 7)
    h = ck["history"][-1]; st.markdown(f"**Corpus:** {ck['corpus']} ({ck['corpus_chars']:,} chars)  \n**Validation:** {h['val_bpc']} bits/char  \n**Training:** {ck['minutes']} min on CPU")
default = "def merge_sorted(" if name.startswith("Python") else "ROMEO:\n"
prompt = st.text_area("Seed prompt", default, height=90)
if st.button("Generate", type="primary") or "out" not in st.session_state:
    t = time.time(); st.session_state.out = sample(m, ck, prompt, n, temp, topk, int(seed)); st.session_state.dt = time.time() - t
st.code(st.session_state.out, language="python" if name.startswith("Python") else None)
st.caption(f"{len(st.session_state.out) - len(prompt)} characters in {st.session_state.dt:.2f}s")
with st.expander("Compare temperatures on this prompt"):
    cols = st.columns(3)
    for c, tt in zip(cols, (.3, .8, 1.3)): c.markdown(f"**T = {tt}**"); c.code(sample(m, ck, prompt, 250, tt, 0, int(seed)), language=None)
