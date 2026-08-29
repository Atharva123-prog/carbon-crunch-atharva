import os
import sys
import json
import warnings
from src.pipeline import ReceiptPipeline
from src.summary import SummaryGenerator

warnings.filterwarnings("ignore")

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    input_dir = "data/raw_receipts"
    output_dir = "outputs"
    json_dir = os.path.join(output_dir, "receipts_json")
    os.makedirs(json_dir, exist_ok=True)

    image_files = [
        os.path.join(input_dir, f) for f in os.listdir(input_dir)
        if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.tiff'))
    ]

    print(f"Initializing Receipt Pipeline for {len(image_files)} receipts...", flush=True)
    pipeline = ReceiptPipeline(gpu=False)

    all_results = []
    for idx, img_path in enumerate(image_files, 1):
        receipt_id = os.path.splitext(os.path.basename(img_path))[0]
        json_path = os.path.join(json_dir, f"{receipt_id}.json")

        if os.path.exists(json_path):
            print(f"[{idx}/{len(image_files)}] Loading existing {receipt_id}.json...", flush=True)
            with open(json_path, "r", encoding="utf-8") as f:
                conf_out = json.load(f)
            all_results.append({
                "receipt_id": receipt_id,
                "confidence_output": conf_out
            })
            continue

        try:
            print(f"[{idx}/{len(image_files)}] Processing {os.path.basename(img_path)}...", flush=True)
            res = pipeline.process_single_receipt(img_path, save_visualization=True, output_dir=output_dir)
            all_results.append(res)
        except Exception as e:
            print(f"Error processing {img_path}: {e}", flush=True)

    summary_gen = SummaryGenerator()
    summary_output = summary_gen.generate_summary(all_results)
    summary_path = summary_gen.save_summary(
        summary_output,
        output_path=os.path.join(output_dir, "expense_summary.json")
    )
    print(f"Batch processing completed successfully! Processed {len(all_results)} receipts.", flush=True)

if __name__ == "__main__":
    main()
