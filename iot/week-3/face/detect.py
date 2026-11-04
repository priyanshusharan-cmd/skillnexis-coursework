"""Face detection with OpenCV's Haar cascade, the detector that runs comfortably on a Raspberry Pi CPU.

    python face/detect.py                 evaluate on bundled images, write results/face_*.png
    python face/detect.py --camera        live: Pi Camera (picamera2) or any USB webcam

Evaluation data (bundled with scikit-image / matplotlib, no download): two portrait photos, and the
`lfw_subset` set of 100 face and 100 non-face patches from Labeled Faces in the Wild.
"""
import argparse
import os
import time

import cv2
import numpy as np

CASCADE = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
EYES = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_eye.xml")


def detect(gray, min_size=40, verify_eyes=False):
    """Returns face boxes (x, y, w, h). Histogram equalisation helps with backlit doorways."""
    g = cv2.equalizeHist(gray)
    faces = CASCADE.detectMultiScale(g, scaleFactor=1.1, minNeighbors=5, minSize=(min_size, min_size))
    faces = [tuple(int(v) for v in f) for f in faces]
    if verify_eyes:   # cheap second opinion: keep boxes with at least one eye in the upper half
        faces = [(x, y, w, h) for x, y, w, h in faces if len(EYES.detectMultiScale(g[y:y + h // 2, x:x + w], 1.1, 3)) > 0]
    return faces


def sample_images():
    import matplotlib
    from skimage import data
    hopper = cv2.imread(os.path.join(matplotlib.get_data_path(), "sample_data", "grace_hopper.jpg"))
    astro = cv2.cvtColor(data.astronaut(), cv2.COLOR_RGB2BGR)
    return {"grace_hopper": hopper, "astronaut": astro}


def evaluate():
    from skimage import data
    os.makedirs("results", exist_ok=True)
    report = []
    for name, img in sample_images().items():
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        t = time.perf_counter()
        faces = detect(gray)
        ms = (time.perf_counter() - t) * 1000
        for x, y, w, h in faces:
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 200, 0), 3)
        cv2.imwrite(f"results/face_{name}.png", img)
        report.append(f"| {name} ({img.shape[1]}x{img.shape[0]}) | {len(faces)} | {ms:.1f} ms |")
    lfw = data.lfw_subset()                      # 200 x 25 x 25, first 100 are faces
    # pad each 25 px patch into a 96 px frame (3x upscale) so the cascade sees a face-sized object in context
    def frame(p):
        canvas = np.full((96, 96), 128, np.uint8)
        canvas[10:85, 10:85] = cv2.resize((p * 255).astype(np.uint8), (75, 75), interpolation=cv2.INTER_LINEAR)
        return canvas
    hits = [len(detect(frame(p), min_size=30)) > 0 for p in lfw]
    tp, fp = sum(hits[:100]), sum(hits[100:])
    lines = ["| Image | Faces found | Time (this PC) |", "|---|---:|---:|"] + report + [
        "", f"LFW subset (25x25 patches, upscaled): detected **{tp}/100** faces, false detections on **{fp}/100** non-face patches."]
    return "\n".join(lines)


def camera_loop():
    try:
        from picamera2 import Picamera2  # Raspberry Pi camera
        cam = Picamera2()
        cam.configure(cam.create_preview_configuration(main={"size": (640, 480), "format": "RGB888"}))
        cam.start()
        grab = lambda: cv2.cvtColor(cam.capture_array(), cv2.COLOR_RGB2BGR)
    except ImportError:
        cap = cv2.VideoCapture(0)
        grab = lambda: cap.read()[1]
    while True:
        frame = grab()
        for x, y, w, h in detect(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)):
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 200, 0), 2)
        cv2.imshow("faces (q to quit)", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--camera", action="store_true")
    args = ap.parse_args()
    if args.camera:
        camera_loop()
    else:
        out = evaluate()
        open("results/face_detection.md", "w").write(out + "\n")
        print(out)
