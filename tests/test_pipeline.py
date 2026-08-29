import os
import pytest
import numpy as np
import cv2
from src.preprocessing import preprocess_image, detect_skew, estimate_blur
from src.ocr_engine import ReceiptOCREngine
from src.extractor import KeyInfoExtractor
from src.confidence import ConfidenceScorer
from src.summary import SummaryGenerator

def test_preprocessing():
    dummy_img = np.ones((500, 500, 3), dtype=np.uint8) * 255
    cv2.putText(dummy_img, "TEST RECEIPT", (50, 200), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 2)
    prep = preprocess_image(dummy_img)
    assert "preprocessed" in prep
    assert "blur_score" in prep
    assert "skew_angle" in prep
    assert isinstance(prep["blur_score"], float)

def test_extractor_store_name():
    extractor = KeyInfoExtractor()
    sample_lines = [
        {"text": "WALMART SUPERCENTER", "confidence": 0.95, "bbox": [10, 10, 200, 30]},
        {"text": "123 MAIN STREET", "confidence": 0.90, "bbox": [10, 45, 200, 20]}
    ]
    res = extractor.extract_store_name(sample_lines, image_height=500)
    assert res["value"] == "WALMART"
    assert res["confidence"] >= 0.90

def test_extractor_date():
    extractor = KeyInfoExtractor()
    sample_lines = [
        {"text": "DATE 2023-08-15 14:30", "confidence": 0.92, "bbox": [10, 60, 200, 20]}
    ]
    res = extractor.extract_date(sample_lines)
    assert "2023-08-15" in res["value"]
    assert res["confidence"] >= 0.85

def test_extractor_items_and_total():
    extractor = KeyInfoExtractor()
    sample_lines = [
        {"text": "WALMART", "confidence": 0.95, "bbox": [10, 10, 200, 30]},
        {"text": "MILK 3.50", "confidence": 0.88, "bbox": [10, 200, 200, 20]},
        {"text": "BREAD 2.50", "confidence": 0.89, "bbox": [10, 230, 200, 20]},
        {"text": "TOTAL 6.00", "confidence": 0.96, "bbox": [10, 400, 200, 30]}
    ]
    items = extractor.extract_items(sample_lines, image_height=500)
    assert len(items) == 2
    total = extractor.extract_total_amount(sample_lines, items, image_height=500)
    assert total["value"] == "6.00"

def test_confidence_scorer():
    scorer = ConfidenceScorer()
    sample_raw = {
        "store_name": {"value": "WALMART", "confidence": 0.95, "source": "dictionary_match"},
        "date": {"value": "2023-08-15", "confidence": 0.90, "source": "regex_pattern"},
        "items": [
            {"name": {"value": "MILK", "confidence": 0.90}, "price": {"value": "3.50", "confidence": 0.90}}
        ],
        "total_amount": {"value": "3.50", "confidence": 0.95, "source": "keyword_anchor"}
    }
    struct, conf = scorer.compute_all(sample_raw)
    assert conf["store_name"]["confidence"] >= 0.70
    assert conf["date"]["confidence"] >= 0.70
    assert conf["total_amount"]["confidence"] >= 0.70
    assert conf["overall_reliability"]["is_reliable"] is True

def test_summary_generator():
    gen = SummaryGenerator()
    dummy_results = [
        {
            "receipt_id": "r1",
            "confidence_output": {
                "store_name": {"value": "WALMART"},
                "date": {"value": "2023-08-15"},
                "total_amount": {"value": "25.50"},
                "items": {"value": [{"name": "MILK", "price": "3.50"}, {"name": "BREAD", "price": "2.50"}]},
                "overall_reliability": {"is_reliable": True}
            }
        },
        {
            "receipt_id": "r2",
            "confidence_output": {
                "store_name": {"value": "TARGET"},
                "date": {"value": "2023-08-16"},
                "total_amount": {"value": "14.50"},
                "items": {"value": [{"name": "MILK", "price": "3.50"}]},
                "overall_reliability": {"is_reliable": True}
            }
        }
    ]
    summary = gen.generate_summary(dummy_results)
    assert summary["financial_summary"]["total_spend"] == 40.00
    assert summary["financial_summary"]["number_of_transactions"] == 2
    assert summary["financial_summary"]["average_transaction_spend"] == 20.00
    assert summary["financial_summary"]["total_items_purchased"] == 3
    assert len(summary["financial_summary"]["purchased_items_breakdown"]) == 2
    assert summary["financial_summary"]["purchased_items_breakdown"][0]["item_name"] == "MILK"
    assert summary["financial_summary"]["purchased_items_breakdown"][0]["quantity_purchased"] == 2
