# Carbon Crunch - Receipt OCR & Financial Information Extraction

A python-based system for extracting structured data from semi-structured receipt images. The pipeline performs image preprocessing, deep-learning OCR with spatial line reconstruction, multi-factor confidence scoring, financial expense summary generation, and interactive data visualization.

---

## Key Capabilities

- Image Preprocessing: Deskewing, Gaussian denoising, contrast enhancement (CLAHE), and focus blur calculation.
- OCR & Spatial Reconstruction: Text detection and recognition using EasyOCR, followed by vertical line-grouping to preserve physical reading order.
- Key Information Extraction: Extraction of vendor name, date, individual line items with prices, and grand total.
- Multi-Factor Confidence Scoring: Combines character OCR probability, format validation, keyword anchor proximity, and item price summation checks.
- Reliability Handling: Low-confidence fields (< 0.70) are flagged for review.
- Financial Analytics: Aggregates spend totals, transaction counts, average spend, and store-level spend breakdowns.
- Web Application: Streamlit UI for visual receipt inspection, bounding box overlays, JSON inspection, and financial reports.

---

## Repository Layout

```text
carbon-intern/
├── app.py                  Streamlit web application
├── run_batch.py            Batch processing entry script
├── DOCUMENTATION.md        Technical documentation report
├── README.md               Project documentation
├── .gitignore              Git ignore rules
├── data/
│   └── raw_receipts/       Receipt image dataset
├── outputs/
│   ├── receipts_json/      Structured JSON results with confidence scores
│   ├── expense_summary.json Aggregated expense metrics
│   └── visualizations/     Bounding box visualization images
├── src/
│   ├── __init__.py         Module exports
│   ├── preprocessing.py    OpenCV preprocessing functions
│   ├── ocr_engine.py       EasyOCR wrapper and line reconstruction
│   ├── extractor.py        Extraction rules for vendor, date, items, and total
│   ├── confidence.py       Field confidence scoring logic
│   ├── summary.py          Financial summary aggregator
│   └── pipeline.py         End-to-end receipt pipeline
└── tests/
    └── test_pipeline.py    Unit tests
```

---

## Setup & Running

### Requirements

```bash
pip install easyocr opencv-python pillow pandas numpy matplotlib streamlit pytest gdown
```

### 1. Batch Execution
To process all receipt images and generate structured outputs:

```bash
python run_batch.py
```

### 2. Interactive Web Application
To launch the Streamlit dashboard:

```bash
streamlit run app.py
```

### 3. Unit Tests
To run verification tests:

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
    "confidence": 0.90,
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
