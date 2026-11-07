"""Streamlit front end for the blood smear analyser. It calls the API (API_URL, default http://localhost:8000);
if the API isn't reachable it runs the same pipeline in-process, so the UI also works on its own.
    streamlit run ui/streamlit_app.py"""
import base64, io, os, sys
import numpy as np, requests, streamlit as st
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); API = os.environ.get("API_URL", "http://localhost:8000")
st.set_page_config(page_title="Blood smear analyser", page_icon="🩸", layout="wide")
st.title("🩸 Blood smear analyser")
st.caption("Finds white blood cells and counts platelets in a stained blood-smear photo (BCCD-style, 640×480). Teaching demo, **not a medical device**.")
with st.sidebar:
    th = st.slider("CNN confidence needed to accept a WBC", .3, .9, .5, .05, help="Platelets use a fixed 0.97, tuned on the training images")
    st.markdown("**How it works**\n1. Purple-stained regions are found with colour thresholds (WBC nuclei, platelets).\n2. A MobileNetV2 classifier checks each candidate.\n3. Accepted cells are boxed and counted.")
    samples = sorted(f for f in os.listdir(os.path.join(HERE, "samples")) if f.lower().endswith((".jpg", ".png"))) if os.path.isdir(os.path.join(HERE, "samples")) else []
    pick = st.selectbox("…or try a test image", ["(upload your own)"] + samples)
up = st.file_uploader("Smear photo", type=["jpg", "jpeg", "png", "bmp", "tiff", "webp"])
data, name = (up.getvalue(), up.name) if up else ((open(os.path.join(HERE, "samples", pick), "rb").read(), pick) if pick != "(upload your own)" else (None, None))
@st.cache_resource
def local():
    sys.path.insert(0, os.path.join(HERE, "..", "src")); import analyze as A; return A, A.CellClassifier()
def run(data, name):
    try:
        r = requests.post(f"{API}/analyze", params=dict(annotated="true", threshold=th), files={"file": (name, data, "image/jpeg" if name.lower().endswith(("jpg", "jpeg")) else "image/png")}, timeout=30)
        if r.status_code != 200: return None, r.json().get("error", {}).get("message", r.text), "api"
        return r.json(), None, "api"
    except requests.RequestException:
        A, clf = local(); rgb = np.asarray(Image.open(io.BytesIO(data)).convert("RGB")); res = A.analyze(rgb, clf, th)
        b = io.BytesIO(); A.draw(rgb, res).save(b, "PNG"); res["annotated_png"] = base64.b64encode(b.getvalue()).decode(); res["warnings"] = []; return res, None, "local"
if data:
    res, error, via = run(data, name)
    if error: st.error(error)
    else:
        c1, c2, c3 = st.columns(3); c1.metric("White blood cells", res["wbc_count"]); c2.metric("Platelets", res["platelet_count"]); c3.metric("Candidates rejected by the CNN", res["rejected_candidates"])
        for w in res.get("warnings", []): st.warning(w)
        a, b = st.columns(2); a.image(data, caption="Uploaded", use_container_width=True); b.image(base64.b64decode(res["annotated_png"]), caption="Blue = WBC, orange = platelet", use_container_width=True)
        with st.expander("Every accepted cell"): st.dataframe([dict(type=c["candidate"], box=str(c["box"]), **{f"p({k})": v for k, v in c["probabilities"].items()}) for c in res["cells"]], use_container_width=True)
        st.caption(f"Analysed via {'the API at ' + API if via == 'api' else 'the in-process pipeline (API not reachable)'}.")
else: st.info("Upload a smear photo or pick a test image in the sidebar.")
