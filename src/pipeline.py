import os
import json
import cv2
import numpy as np
from .preprocessing import preprocess_image
from .ocr_engine import ReceiptOCREngine
from .extractor import KeyInfoExtractor
from .confidence import ConfidenceScorer
from .summary import SummaryGenerator

class ReceiptPipeline:
    def __init__(self, gpu=False):
        self.ocr_engine = ReceiptOCREngine(gpu=gpu)
        self.extractor = KeyInfoExtractor()
        self.confidence_scorer = ConfidenceScorer(low_conf_threshold=0.70)
        self.summary_generator = SummaryGenerator()

    def process_single_receipt(self, image_path, save_visualization=True, output_dir="outputs"):
        receipt_id = os.path.splitext(os.path.basename(image_path))[0]
        prep_results = preprocess_image(image_path)
        ocr_results = self.ocr_engine.process(prep_results["preprocessed"])
        extracted_raw = self.extractor.extract_all(ocr_results, prep_results["preprocessed"].shape[:2])
        struct_output, conf_output = self.confidence_scorer.compute_all(extracted_raw)

        vis_path = None
        if save_visualization:
            vis_dir = os.path.join(output_dir, "visualizations")
            os.makedirs(vis_dir, exist_ok=True)
            vis_path = os.path.join(vis_dir, f"{receipt_id}_bbox.jpg")
            self.draw_visualizations(prep_results["preprocessed"], ocr_results["text_boxes"], vis_path)

        result_dict = {
            "receipt_id": receipt_id,
            "image_path": image_path,
            "structured_output": struct_output,
            "confidence_output": conf_output,
            "ocr_confidence": ocr_results["ocr_confidence"],
            "blur_score": prep_results["blur_score"],
            "skew_angle": prep_results["skew_angle"],
            "visualization_path": vis_path
        }

        json_dir = os.path.join(output_dir, "receipts_json")
        os.makedirs(json_dir, exist_ok=True)
        json_path = os.path.join(json_dir, f"{receipt_id}.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(conf_output, f, indent=2)

        return result_dict

    def draw_visualizations(self, image, text_boxes, output_path):
        vis_img = image.copy()
        for box in text_boxes:
            pts = np.array(box["bbox"], np.int32).reshape((-1, 1, 2))
            cv2.polylines(vis_img, [pts], True, (0, 255, 0), 2)
            x, y = box["bbox"][0]
            label = f"{box['text'][:15]} ({box['confidence']:.2f})"
            cv2.putText(vis_img, label, (x, max(15, y - 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 0, 0), 1)
        cv2.imwrite(output_path, vis_img)

    def process_directory(self, input_dir="data/raw_receipts", output_dir="outputs"):
        if not os.path.exists(input_dir):
            raise FileNotFoundError(f"Directory not found: {input_dir}")

        image_files = [
            os.path.join(input_dir, f) for f in os.listdir(input_dir)
            if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.tiff'))
        ]

        all_results = []
        for idx, img_path in enumerate(image_files, 1):
            try:
                print(f"[{idx}/{len(image_files)}] Processing {os.path.basename(img_path)}...", flush=True)
                res = self.process_single_receipt(img_path, save_visualization=True, output_dir=output_dir)
                all_results.append(res)
            except Exception as e:
                print(f"Error processing {img_path}: {e}", flush=True)

        summary_output = self.summary_generator.generate_summary(all_results)
        summary_path = self.summary_generator.save_summary(
            summary_output,
            output_path=os.path.join(output_dir, "expense_summary.json")
        )

        return {
            "processed_count": len(all_results),
            "receipt_results": all_results,
            "expense_summary": summary_output,
            "summary_file": summary_path
        }

if __name__ == "__main__":
    pipeline = ReceiptPipeline(gpu=False)
    results = pipeline.process_directory("data/raw_receipts", "outputs")
    print(f"Pipeline executed successfully. Processed {results['processed_count']} receipts.")
