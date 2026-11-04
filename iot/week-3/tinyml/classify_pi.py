"""Raspberry Pi side: classify a photo of a handwritten digit with the int8 model.
Needs only:  pip install ai-edge-litert opencv-python-headless numpy

    python classify_pi.py photo.jpg            (or --camera to grab one frame from the Pi Camera)
"""
import sys

import cv2
import numpy as np
from tflite_utils import TFLiteModel


def preprocess(bgr):
    """Dark ink on light paper -> the 8x8, 0..1, ink-bright format the model was trained on."""
    g = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    _, th = cv2.threshold(cv2.GaussianBlur(g, (5, 5), 0), 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    ys, xs = np.nonzero(th)
    if len(xs) == 0:
        raise ValueError("no ink found")
    crop = th[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    side = max(crop.shape) + 8
    sq = np.zeros((side, side), np.uint8)
    y0, x0 = (side - crop.shape[0]) // 2, (side - crop.shape[1]) // 2
    sq[y0:y0 + crop.shape[0], x0:x0 + crop.shape[1]] = crop
    return (cv2.resize(sq, (8, 8), interpolation=cv2.INTER_AREA) / 255.0).astype(np.float32)[..., None]


if __name__ == "__main__":
    if "--camera" in sys.argv:
        from picamera2 import Picamera2
        cam = Picamera2()
        cam.start()
        img = cv2.cvtColor(cam.capture_array(), cv2.COLOR_RGB2BGR)
    else:
        img = cv2.imread(sys.argv[1])
    p = TFLiteModel("digits_int8.tflite").predict_proba(preprocess(img))
    print(f"digit {p.argmax()} ({p.max():.0%} confident)")
