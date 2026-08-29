# CARBON CRUNCH - Receipt OCR & Financial Information Extraction System

An automated, confidence-aware receipt processing system built to extract structured data from semi-structured receipt images, assign multi-factor confidence scores, flag reliability risks, generate financial expense summaries, and provide an interactive web dashboard.

---

## Features

- **Computer Vision Preprocessing**: Automatic image deskewing ($\pm 45^\circ$), focus blur estimation via Laplacian variance, Gaussian denoising, and CLAHE contrast enhancement for faint thermal receipts.
- **Deep Learning OCR & Line Reconstruction**: Integrates EasyOCR with a spatial bounding-box line grouping algorithm that reconstitutes disjointed character tokens into physical reading order.
- **Key Information Extraction**:
  - Store / Vendor Name (header spatial heuristics + retail dictionary matching)
  - Transaction Date (multi-pattern regex engine for ISO and standard date formats)
  - Line Items & Item Prices (body line scanning & description/price pairing)
  - Total Amount (priority keyword anchors: `GRAND TOTAL`, `BALANCE DUE`, `TOTAL AMOUNT`, `TOTAL`)
- **Multi-Factor Confidence Scoring**: Field confidence scores ($0.0 - 1.0$) combining OCR probability ($C_{ocr}$), pattern compliance ($C_{pattern}$), keyword anchor proximity ($C_{heuristic}$), and mathematical item price cross-validation ($\sum \text{items} \approx \text{total}$). Low-confidence fields ($<0.70$) are flagged.
- **Financial Expense Summary Aggregator**: Compiles total spend across all processed receipts, transaction counts, average spend, and store-by-store breakdown.
- **Interactive Web Dashboard**: Streamlit interface for side-by-side receipt image visualizer, bounding box overlays, field confidence inspection, and expense analytics charts.

---

## Directory Structure

```
carbon-intern/
├── app.py                  # Streamlit Interactive Web Application
├── run_batch.py            # Batch processing driver script
├── DOCUMENTATION.md        # Technical approach & system evaluation report
├── README.md               # Repository documentation
├── .gitignore              # Git ignore configuration
├── data/
│   └── raw_receipts/       # Receipt image dataset (49 images)
├── outputs/
│   ├── receipts_json/      # Extracted field JSON outputs with confidence scores
│   ├── expense_summary.json# Aggregated financial expense metrics
│   └── visualizations/     # Rendered bounding box overlay images
├── src/
│   ├── __init__.py         # Package exports
│   ├── preprocessing.py    # Image deskewing, denoising, CLAHE contrast
│   ├── ocr_engine.py       # EasyOCR wrapper & spatial line grouping
│   ├── extractor.py        # Store, Date, Items, and Total extraction logic
│   ├── confidence.py       # Multi-factor confidence scorer & reliability flagger
│   ├── summary.py          # Expense summary aggregator
│   └── pipeline.py         # End-to-end receipt pipeline driver
└── tests/
    └── test_pipeline.py    # Pytest unit verification test suite
```

---

## Installation & Setup

1. **Clone Repository**:
   ```bash
   git clone https://github.com/Atharva123-prog/carbon-crunch-atharva.git
   cd carbon-crunch-atharva
   ```

2. **Install Dependencies**:
   ```bash
   pip install easyocr opencv-python pillow pandas numpy matplotlib streamlit pytest gdown
   ```

---

## Usage Guide

### 1. Run Batch Extraction Pipeline
To process all receipt images and generate JSON outputs + expense summary:
```bash
python run_batch.py
```

Outputs will be saved under:
- `outputs/receipts_json/<receipt_id>.json`
- `outputs/expense_summary.json`
- `outputs/visualizations/<receipt_id>_bbox.jpg`

### 2. Launch Streamlit Web Dashboard
To view receipts, bounding box overlays, field confidence scores, and expense charts interactively:
```bash
streamlit run app.py
```

### 3. Run Automated Unit Tests
To verify all pipeline units:
```bash
python -m pytest tests/test_pipeline.py
```

---

## Sample JSON Output Format

```json
{
  "store_name": {
    "value": "WALMART",
    "confidence": 0.95,
    "low_confidence": false
  },
  "date": {
    "value": "2023-08-15",
    "confidence": 0.90,
    "low_confidence": false
  },
  "items": {
    "value": [
      {
        "name": "MILK",
        "price": "3.50"
      },
      {
        "name": "BREAD",
        "price": "2.50"
      }
    ],
    "confidence": 0.895,
    "low_confidence": false
  },
  "total_amount": {
    "value": "6.00",
    "confidence": 0.96,
    "low_confidence": false
  },
  "overall_reliability": {
    "average_confidence": 0.93,
    "is_reliable": true,
    "warnings": []
  }
}
```
