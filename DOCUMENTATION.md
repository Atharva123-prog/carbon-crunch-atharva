# CARBON CRUNCH - Technical Documentation & System Report

## 1. Executive Summary & Objective

This report details the design, implementation, and evaluation of an end-to-end, confidence-aware receipt processing system. The solution ingests semi-structured receipt images, performs computer vision pre-processing, detects and recognizes text using EasyOCR, extracts key financial fields (Store/Vendor Name, Transaction Date, Line Items, and Total Amount), assigns multi-factor confidence scores (0.0 to 1.0), flags low-confidence reliability risks, and compiles aggregate financial expense summaries.

---

## 2. Technical Approach & Pipeline Architecture

The system is engineered following a modular micro-architecture:

```
[Raw Receipt Image]
       │
       ▼
┌────────────────────────────────────────┐
│ 1. Computer Vision Image Preprocessing  │
│    - Hough Line & MinRect Deskewing     │
│    - Bilateral Denoising Filter         │
│    - CLAHE Contrast Normalization       │
│    - Adaptive Threshold Binarization    │
└──────────────────┬─────────────────────┘
                   │
                   ▼
┌────────────────────────────────────────┐
│ 2. OCR & Spatial Reconstruction        │
│    - EasyOCR (CRAFT + ResNet CRNN)     │
│    - Bounding Box Coordinate Sorting    │
│    - Dynamic Vertical Line Grouping    │
└──────────────────┬─────────────────────┘
                   │
                   ▼
┌────────────────────────────────────────┐
│ 3. Key Information Extraction Engine   │
│    - Store Name: Spatial + Dictionary  │
│    - Date: Multi-format ISO Regex      │
│    - Items: Body Scan & Line Parsing   │
│    - Total Amount: Keyword Anchor      │
└──────────────────┬─────────────────────┘
                   │
                   ▼
┌────────────────────────────────────────┐
│ 4. Multi-Factor Confidence & Scoring   │
│    - C_ocr: Engine Character Score     │
│    - C_pattern: Format & Math Check    │
│    - C_heuristic: Anchor Keyword Score │
│    - Low-Confidence Flagging (<0.70)   │
└──────────────────┬─────────────────────┘
                   │
                   ▼
┌────────────────────────────────────────┐
│ 5. Structured Outputs & Dashboard      │
│    - JSON Outputs per Receipt           │
│    - Expense Summary Aggregator        │
│    - Streamlit Visual Dashboard        │
└────────────────────────────────────────┘
```

### Key Modules:
- **`src/preprocessing.py`**: Performs automatic image rotation correction (deskewing), focus quality measurement via Laplacian variance, bilateral noise reduction, and CLAHE contrast enhancement for low-light/faint thermal receipts.
- **`src/ocr_engine.py`**: Wraps EasyOCR with a spatial bounding box sorting algorithm that reconstitutes disjointed character tokens into ordered horizontal line structures.
- **`src/extractor.py`**: Applies multi-layered extraction heuristics for Store Name, Date, Items, and Total Amount.
- **`src/confidence.py`**: Combines character OCR probability, regex pattern match compliance, and mathematical cross-validation ($\sum \text{items} \approx \text{total}$) into field-level confidence metrics $[0.0, 1.0]$.
- **`src/summary.py`**: Aggregates spend totals, average transaction values, transaction counts, and store-wise spend breakdowns.
- **`app.py`**: Interactive Streamlit web application providing side-by-side receipt visualizer, bounding box overlays, field confidence inspection, and expense charts.

---

## 3. Tools & Technologies Used

| Category | Tool / Library | Usage Rationale |
| :--- | :--- | :--- |
| **Programming Language** | Python 3.13 | Core system development |
| **Computer Vision** | OpenCV (`cv2`) & Pillow | Deskewing, CLAHE, Bilateral filtering, contour analysis |
| **OCR Engine** | EasyOCR (PyTorch) | Deep learning CRAFT detector & CRNN text recognizer |
| **Numerical Processing** | NumPy & Pandas | Bounding box spatial calculations & data tabularization |
| **Web UI Dashboard** | Streamlit | Interactive visualization, bounding box overlay, analytics UI |
| **Testing Suite** | Pytest | Unit testing for pipeline components |

---

## 4. Challenges Faced & Solutions

### Challenge 1: Layout & Orientation Skew Variations
- **Issue**: Real-world receipt images arrive rotated, slanted, or angled.
- **Solution**: Developed Hough line transform angle estimation and OpenCV warpAffine deskewing to align text horizontally ($\pm 45^\circ$).

### Challenge 2: Disjointed OCR Text Ordering
- **Issue**: Standard OCR outputs text tokens out of physical line reading order.
- **Solution**: Designed a spatial line-grouping algorithm that calculates average text box height and merges bounding boxes sharing horizontal Y-centers into ordered line arrays.

### Challenge 3: Ambiguity Between Subtotal, Tax, and Grand Total
- **Issue**: Receipts often list multiple monetary values ("Subtotal", "Tax", "Net Amount", "Grand Total").
- **Solution**: Prioritized explicit total keyword anchors ("GRAND TOTAL", "BALANCE DUE", "TOTAL AMOUNT"), fallback to maximum monetary figure in the lower 40% of the image, and validated total against item price summation.

### Challenge 4: Low-Contrast Faint Thermal Receipts
- **Issue**: Thermal paper receipts fade over time or suffer from harsh shadow gradients.
- **Solution**: Applied Contrast Limited Adaptive Histogram Equalization (CLAHE) with clip limit 2.5 and bilateral filtering to sharpen character boundaries without magnifying paper grain.

---

## 5. Future Enhancements & Improvements

1. **Multimodal Vision-Language Model Integration**: Integrate lightweight LayoutLMv3 or Donut fine-tuned model as an additional hybrid extraction path for edge cases.
2. **Human-in-the-Loop Feedback Loop**: Allow users to edit low-confidence fields (<0.70) in the Streamlit UI and save correction records for active learning model fine-tuning.
3. **Multi-Currency Support**: Expand regex patterns and financial summary aggregators to support automatic currency symbol detection ($, €, £, ₹, ¥).
