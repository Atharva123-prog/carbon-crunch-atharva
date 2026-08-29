# Receipt Information Extraction & Financial Summary Pipeline

## 1. Project Overview

This document describes the design, implementation, and evaluation of a system built to extract structured data from semi-structured receipt images. The system processes raw receipt images, detects and reads text via OCR, extracts key metadata (Store Name, Date, Items, and Total Amount), assesses field-level confidence scores, and compiles aggregate financial expense summaries.

---

## 2. System Architecture

The pipeline consists of five key functional modules:

```text
+------------------------+     +------------------------+     +------------------------+
| 1. Image Preprocessing | --> | 2. OCR & Line Grouping | --> | 3. Field Extraction    |
| - Deskewing            |     | - EasyOCR Detector     |     | - Vendor Name          |
| - Gaussian Denoising   |     | - Spatial Reconstruction|    | - Date Parsing         |
| - CLAHE Contrast       |     | - Bounding Box Ordering|     | - Line Items & Prices  |
+------------------------+     +------------------------+     | - Total Amount         |
                                                              +-----------+------------+
                                                                          |
+------------------------+     +------------------------+                 v
| 5. Output & Dashboard  | <-- | 4. Financial Summary   | <-- +------------------------+
| - Structured JSON      |     | - Total Spend          |     | 4. Confidence Scorer   |
| - Streamlit Dashboard  |     | - Spend per Vendor     |     | - OCR Probability      |
| - Visualization Images |     | - Transaction Analytics|     | - Pattern Matching     |
+------------------------+     +------------------------+     | - Low-Conf Flags (<0.7)|
                                                              +------------------------+
```

### Module Descriptions

- `src/preprocessing.py`: Provides image transformations including skew detection using Hough lines, rotation correction, blur estimation using Laplacian variance, Gaussian denoising, and CLAHE contrast enhancement for thermal paper receipts.
- `src/ocr_engine.py`: Integrates EasyOCR and implements spatial bounding box sorting to reconstitute disjointed character tokens into horizontal text lines.
- `src/extractor.py`: Implements heuristics and pattern matching rules for Store Name, Date, Items (descriptions and prices), and Total Amount.
- `src/confidence.py`: Computes composite confidence scores (0.0 to 1.0) using OCR probabilities, regex compliance, keyword proximity, and mathematical validation (comparing item sum against grand total). Flags fields with confidence below 0.70.
- `src/summary.py`: Aggregates metrics across processed receipts, calculating overall spend, average transaction value, transaction counts, and vendor-wise breakdowns.
- `app.py`: Streamlit web dashboard providing visual comparison of original vs preprocessed images, bounding box visualization overlays, JSON data views, and financial reports.

---

## 3. Technical Stack

| Component | Library / Framework | Function |
| :--- | :--- | :--- |
| Core Language | Python 3.13 | Primary development language |
| Computer Vision | OpenCV, Pillow | Image transformation and bounding box drawing |
| OCR Engine | EasyOCR | Text detection (CRAFT) and recognition (CRNN) |
| Data Handling | NumPy, Pandas | Array operations and tabular aggregation |
| User Interface | Streamlit | Web dashboard interface |
| Testing | Pytest | Automated unit testing |

---

## 4. Engineering Challenges & Solutions

### Line Reconstruction from Disjointed OCR Output
- Problem: OCR engines return isolated text boxes out of natural reading order.
- Solution: Developed a spatial grouping algorithm that calculates median character height and clusters bounding boxes sharing Y-center coordinates into ordered horizontal lines.

### Ambiguity Between Subtotal, Tax, and Grand Total
- Problem: Receipts list multiple numeric totals.
- Solution: Implemented keyword anchor priority ("GRAND TOTAL", "BALANCE DUE", "TOTAL AMOUNT"), fallback to lower-quadrant monetary figures, and mathematical validation against line item sums.

### Uneven Lighting and Thermal Paper Fading
- Problem: Receipt images suffer from shadows and faded text.
- Solution: Applied Contrast Limited Adaptive Histogram Equalization (CLAHE) combined with Gaussian blur to sharpen contrast around character edges.

---

## 5. Future Enhancements

- Multimodal LLM / VLM Fallback: Add vision-language model integration (e.g. Donut or LayoutLM) as a secondary validation step for complex layouts.
- User Review Workflow: Allow users to edit low-confidence fields directly in the Streamlit UI.
- Multi-Currency Support: Expand regex rules to automatically parse international currency symbols ($, EUR, GBP, JPY).
