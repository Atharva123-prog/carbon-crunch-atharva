import easyocr
import numpy as np
import cv2

class ReceiptOCREngine:
    def __init__(self, languages=['en'], gpu=False):
        self.reader = easyocr.Reader(languages, gpu=gpu, verbose=False)

    def extract_text_boxes(self, image):
        if isinstance(image, str):
            image = cv2.imread(image)
        results = self.reader.readtext(image, canvas_size=768, mag_ratio=1.0)
        text_boxes = []
        for box, text, prob in results:
            pts = np.array(box, dtype=np.int32).tolist()
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            x_min, y_min = min(xs), min(ys)
            x_max, y_max = max(xs), max(ys)
            w = x_max - x_min
            h = y_max - y_min
            text_boxes.append({
                "text": text.strip(),
                "confidence": float(prob),
                "bbox": pts,
                "box_xywh": [x_min, y_min, w, h],
                "y_center": y_min + h / 2.0,
                "x_center": x_min + w / 2.0,
                "height": h
            })
        return text_boxes

    def group_text_into_lines(self, text_boxes):
        if not text_boxes:
            return []
        sorted_boxes = sorted(text_boxes, key=lambda b: (b["y_center"], b["box_xywh"][0]))
        avg_height = np.median([b["height"] for b in sorted_boxes]) if sorted_boxes else 15
        line_threshold = max(8.0, avg_height * 0.5)

        lines = []
        current_line = []

        for box in sorted_boxes:
            if not current_line:
                current_line.append(box)
            else:
                line_y_center = np.mean([b["y_center"] for b in current_line])
                if abs(box["y_center"] - line_y_center) <= line_threshold:
                    current_line.append(box)
                else:
                    current_line.sort(key=lambda b: b["box_xywh"][0])
                    lines.append(current_line)
                    current_line = [box]

        if current_line:
            current_line.sort(key=lambda b: b["box_xywh"][0])
            lines.append(current_line)

        structured_lines = []
        for line_boxes in lines:
            line_text = " ".join([b["text"] for b in line_boxes if b["text"]])
            line_conf = float(np.mean([b["confidence"] for b in line_boxes])) if line_boxes else 0.0
            xs = [b["box_xywh"][0] for b in line_boxes] + [b["box_xywh"][0] + b["box_xywh"][2] for b in line_boxes]
            ys = [b["box_xywh"][1] for b in line_boxes] + [b["box_xywh"][1] + b["box_xywh"][3] for b in line_boxes]
            line_bbox = [min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)]
            structured_lines.append({
                "text": line_text,
                "confidence": line_conf,
                "bbox": line_bbox,
                "words": line_boxes,
                "y_center": float(np.mean([b["y_center"] for b in line_boxes]))
            })
        return structured_lines

    def process(self, image):
        text_boxes = self.extract_text_boxes(image)
        lines = self.group_text_into_lines(text_boxes)
        full_text = "\n".join([line["text"] for line in lines])
        avg_conf = float(np.mean([b["confidence"] for b in text_boxes])) if text_boxes else 0.0
        return {
            "text_boxes": text_boxes,
            "lines": lines,
            "full_text": full_text,
            "ocr_confidence": avg_conf
        }
