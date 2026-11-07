# Capstone report: a blood-smear analyser

> A teaching and research demo trained on one small public dataset. **It is not a medical device** and must not be
> used for diagnosis.

## 1. Problem
A complete blood count starts with looking at a stained smear: finding the white blood cells (WBCs) and estimating
platelets. The goal is a service that takes a smear photo and returns **where the WBCs are** and **how many
platelets** are in the field, with the evidence (boxes and confidences), behind a documented API and a simple UI.

## 2. Data
**BCCD** (`github.com/Shenggan/BCCD_Dataset`, MIT licence): 364 light-microscope images (640×480) of stained
peripheral blood with VOC boxes: 4,155 RBC, 372 WBC and 361 platelet annotations. The official image-level splits
are used, so no cell from a test image is ever seen in training:

| Split | Images | Cell crops (RBC / WBC / platelets) |
|---|---|---|
| train | 205 | 2,804 (2,381 / 214 / 209) |
| val | 87 | 1,137 |
| test | 72 | 945 |

**Known data problems, and how they shaped the design:**
1. **RBC boxes are incomplete:** many visible RBCs are not annotated, and they overlap heavily. An RBC count could
   not be evaluated honestly, so **the system doesn't count RBCs**.
2. **Class imbalance:** RBCs outnumber the other classes 11:1, handled with class-weighted training and reported
   as macro-F1.
3. **Small size:** 205 training images, so transfer learning is used, with no training from scratch.

## 3. Approach
```
smear photo ──► stain segmentation (HSV) ──► candidates ──► MobileNetV2 cell classifier (TFLite) ──► accepted cells ──► counts + boxes
                 purple = nuclei/platelets     WBC: area ≥ 3,000 px            RBC / WBC / Platelets
                                               platelet: 150–1,500 px
```
* **Candidates** ([`src/cells.py`](src/cells.py)): in Wright/Giemsa stain, WBC nuclei and platelets are strongly
  purple and RBCs are pale pink. A saturation and hue threshold, morphology and connected components give large
  components (WBC nuclei, whose box is scaled ×1.25 to cover the whole cell) and small ones (platelet candidates).
  This step needs no training data and is fast and explainable.
* **Classifier** ([`src/train_classifier.py`](src/train_classifier.py)): MobileNetV2 (ImageNet weights) on 96×96
  cell crops.
  1. Stage A: a frozen backbone and a class-weighted head on cached features.
  2. Stage B: fine-tune the last 30 layers with augmentation. Flips and 90° rotations are safe because cells have
     no orientation; brightness and contrast cover stain variation.
  3. The stage is selected on validation macro-F1, then the model is exported to **TFLite with dynamic-range int8**
     (2.4 MB).
* **Decision rules:** a WBC candidate is accepted if p(WBC) ≥ 0.5. A platelet candidate is accepted if
  p(Platelets) ≥ 0.97 and its area is 150–1,500 px.
* **Every tuned number was chosen on train+val only:**
  * the WBC box scale ([`results/wbc_scale.json`](results/wbc_scale.json));
  * the platelet area range and threshold ([`src/tune_platelets.py`](src/tune_platelets.py) →
    [`results/platelet_tuning.json`](results/platelet_tuning.json)).

## 4. Results (72 test images, 945 test cells)
**Cell classifier** ([`results/classifier.json`](results/classifier.json)):

| | Stage A (frozen) | **Stage B (fine-tuned, deployed)** | TFLite int8 |
|---|---|---|---|
| Macro-F1 | 0.971 | **0.988** | |
| Accuracy | | 99.7 % | 99.8 % (agrees with Keras on 99.9 % of crops) |

Per class (precision / recall): RBC 1.000 / 0.999 · WBC 0.986 / 0.986 · platelets 0.971 / 0.986.
Confusion matrix: [`results/classifier_confusion.png`](results/classifier_confusion.png).

**Whole pipeline** ([`results/pipeline.json`](results/pipeline.json)):

| Task | Result | Baseline |
|---|---|---|
| WBC localisation (IoU ≥ 0.5) | **precision 0.947, recall 1.000**, mean IoU 0.81 | |
| Platelet count per image | **MAE 0.56**, exact on 58 % of images | always predicting the training mean: MAE 0.88 |

![Examples](results/examples.png)

## 5. What went wrong and what I changed
* **First platelet rule:** every small purple blob of 40 px or more, accepted at p ≥ 0.5. It **over-counted badly
  (MAE 1.50, worse than the 0.88 baseline)**, because stain debris and RBC inclusions look like tiny purple dots.
  The rule was re-tuned **on train+val only** (minimum area 150 px, p ≥ 0.97), and the test MAE fell to 0.56.
* **Transparency note:** I did look at the first rule's test score before re-tuning. The new values were chosen on
  train+val and generalised (train+val MAE 0.64 → test 0.56), but strictly the test set is no longer completely
  untouched for the platelet rule.
* **Remaining errors:**
  * WBC "false positives": 4 of 75 predicted boxes. At least one is an annotation gap, not a model error:
    BloodImage_00327 clearly shows a WBC (see the figure) but has no WBC box in BCCD.
  * Platelets in clumps or touching an RBC are missed (BloodImage_00327: annotated 2, found 0).

## 6. Deployment
* **API** ([`api/app.py`](api/app.py), FastAPI):
  * endpoints: `GET /health` (with counters), `POST /analyze` (boxes, counts, optional annotated PNG),
    `POST /classify` (one crop);
  * JSON errors for missing or empty files (400), files over 8 MB (413), unaccepted types (415), and corrupt or
    tiny images and bad parameters (422); unexpected failures return 500 without leaking internals;
  * warnings when the image size differs from the 640×480 training set;
  * request IDs and timing headers on every response; 5 tests in [`tests/`](tests/).
* **UI** ([`ui/streamlit_app.py`](ui/streamlit_app.py)): upload a smear or pick a sample, then see the counts, the
  annotated image and the per-cell probabilities. It calls the API, or falls back to the in-process pipeline.
* **Containers:** one [`Dockerfile`](Dockerfile) (non-root, health check) and
  [`docker-compose.yml`](docker-compose.yml) running the API on :8000 and the UI on :8501.
  `docker compose up --build` starts both.
* **Not run here:** the Docker build. The sandbox can't reach Docker Hub to pull the base image. The API and UI
  were run and tested directly.
* **Free hosting:** Render or Hugging Face Spaces (Docker), with your account. The image only needs the 2.4 MB
  TFLite model, not TensorFlow.

![UI](ui/screenshot.png)

## 7. Limitations and next steps
* One dataset, one microscope, one magnification. A new lab's stain or camera needs re-tuning of the colour
  thresholds and probably fine-tuning.
* There's no WBC subtype classification (neutrophil, lymphocyte, …), because BCCD doesn't label subtypes. A labelled
  WBC dataset would make that the natural next model.
* A learned detector (for example YOLO or Faster R-CNN) would replace the colour rules and handle clumps, but needs
  pretrained detection weights. Those can't be downloaded in this sandbox, and the data is small.
