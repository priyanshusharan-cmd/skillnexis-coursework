"""API tests for the capstone service.   pytest -q tests"""
import io, os, sys
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from fastapi.testclient import TestClient
from api.app import app
c = TestClient(app); S = os.path.join(os.path.dirname(__file__), "..", "ui", "samples")
def sample(): f = sorted(x for x in os.listdir(S) if x.endswith(".jpg"))[0]; return open(os.path.join(S, f), "rb").read()
def test_health(): assert c.get("/health").json()["model_loaded"] is True
def test_analyze_sample():
    r = c.post("/analyze?annotated=true", files={"file": ("smear.jpg", sample(), "image/jpeg")}); j = r.json()
    assert r.status_code == 200 and j["wbc_count"] >= 1 and "annotated_png" in j and j["image_size"] == [640, 480] and j["warnings"] == []
    for cell in j["cells"]: assert len(cell["box"]) == 4 and abs(sum(cell["probabilities"].values()) - 1) < 0.01
def test_classify_crop():
    img = Image.open(io.BytesIO(sample())).convert("RGB")
    j = c.post("/analyze", files={"file": ("s.jpg", sample(), "image/jpeg")}).json(); box = [x for x in j["cells"] if x["candidate"] == "WBC"][0]["box"]
    b = io.BytesIO(); img.crop(box).save(b, "PNG"); r = c.post("/classify", files={"file": ("wbc.png", b.getvalue(), "image/png")})
    assert r.status_code == 200 and r.json()["label"] == "WBC"
def test_errors():
    assert c.post("/analyze", files={"file": ("a.txt", b"hi", "text/plain")}).status_code == 415
    assert c.post("/analyze", files={"file": ("a.png", b"", "image/png")}).status_code == 400
    assert c.post("/analyze", files={"file": ("a.png", b"\x89PNG\r\n\x1a\nxx", "image/png")}).json()["error"]["code"] == "unreadable_image"
    assert c.post("/analyze").json()["error"]["code"] == "missing_file"
    small = io.BytesIO(); Image.fromarray(np.zeros((50, 50, 3), np.uint8)).save(small, "PNG")
    assert c.post("/analyze", files={"file": ("s.png", small.getvalue(), "image/png")}).json()["error"]["code"] == "image_too_small"
    assert c.post("/analyze?threshold=5", files={"file": ("s.jpg", sample(), "image/jpeg")}).status_code == 422
def test_other_size_warns():
    img = Image.open(io.BytesIO(sample())).resize((1280, 960)); b = io.BytesIO(); img.save(b, "JPEG")
    j = c.post("/analyze", files={"file": ("big.jpg", b.getvalue(), "image/jpeg")}).json(); assert j["warnings"]
