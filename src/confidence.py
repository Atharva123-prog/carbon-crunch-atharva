import re

class ConfidenceScorer:
    def __init__(self, low_conf_threshold=0.70):
        self.low_conf_threshold = low_conf_threshold

    def score_store_name(self, store_data):
        val = store_data.get("value", "UNKNOWN")
        raw_conf = store_data.get("confidence", 0.0)
        source = store_data.get("source", "")

        if val == "UNKNOWN" or not val:
            return 0.0, ["Missing store name"]

        warnings = []
        pattern_score = 0.5
        if source == "dictionary_match":
            pattern_score = 1.0
        elif len(val) >= 4 and val.isupper():
            pattern_score = 0.85
        elif len(val) >= 3:
            pattern_score = 0.70
        else:
            pattern_score = 0.40
            warnings.append("Short or ambiguous store name")

        composite = 0.4 * raw_conf + 0.6 * pattern_score
        final_score = round(min(1.0, max(0.0, composite)), 2)

        if final_score < self.low_conf_threshold:
            warnings.append("Low confidence store name")

        return final_score, warnings

    def score_date(self, date_data):
        val = date_data.get("value", "UNKNOWN")
        raw_conf = date_data.get("confidence", 0.0)
        source = date_data.get("source", "")

        if val == "UNKNOWN" or not val:
            return 0.0, ["Missing transaction date"]

        warnings = []
        pattern_score = 0.0
        if re.search(r'\b20\d{2}[-\/\.](?:0[1-9]|1[0-2])[-\/\.](?:0[1-9]|[12]\d|3[01])\b', val):
            pattern_score = 1.0
        elif re.search(r'\b\d{1,2}[-\/\.]\d{1,2}[-\/\.]\d{2,4}\b', val):
            pattern_score = 0.90
        elif re.search(r'[A-Za-z]{3}', val):
            pattern_score = 0.85
        else:
            pattern_score = 0.50
            warnings.append("Unstandardized date format")

        composite = 0.35 * raw_conf + 0.65 * pattern_score
        final_score = round(min(1.0, max(0.0, composite)), 2)

        if final_score < self.low_conf_threshold:
            warnings.append("Low confidence date")

        return final_score, warnings

    def score_total_amount(self, total_data, items_data):
        val = total_data.get("value", "0.00")
        raw_conf = total_data.get("confidence", 0.0)
        source = total_data.get("source", "")

        warnings = []
        try:
            total_val = float(val)
        except ValueError:
            return 0.0, ["Invalid total amount value"]

        if total_val <= 0.0:
            return 0.0, ["Total amount is zero or negative"]

        pattern_score = 0.60
        if source == "keyword_anchor":
            pattern_score = 0.95
        elif source == "max_monetary_fallback":
            pattern_score = 0.70
            warnings.append("Total amount inferred without keyword anchor")

        if items_data:
            item_prices = []
            for it in items_data:
                try:
                    item_prices.append(float(it["price"]["value"]))
                except (KeyError, ValueError):
                    continue

            if item_prices:
                item_sum = sum(item_prices)
                if abs(item_sum - total_val) < 0.05:
                    pattern_score = min(1.0, pattern_score + 0.15)
                elif total_val < item_sum:
                    pattern_score = max(0.3, pattern_score - 0.25)
                    warnings.append("Total amount is less than calculated sum of item prices")

        composite = 0.40 * raw_conf + 0.60 * pattern_score
        final_score = round(min(1.0, max(0.0, composite)), 2)

        if final_score < self.low_conf_threshold:
            warnings.append("Low confidence total amount")

        return final_score, warnings

    def score_items(self, items_data):
        if not items_data:
            return 0.0, ["No items extracted"]

        item_scores = []
        warnings = []

        for idx, item in enumerate(items_data):
            name_conf = item["name"].get("confidence", 0.5)
            price_conf = item["price"].get("confidence", 0.5)
            p_val = item["price"].get("value", "0.00")

            try:
                pf = float(p_val)
                price_pattern = 1.0 if pf > 0 else 0.3
            except ValueError:
                price_pattern = 0.0

            item_composite = 0.5 * name_conf + 0.5 * (0.5 * price_conf + 0.5 * price_pattern)
            item_scores.append(round(min(1.0, max(0.0, item_composite)), 2))

        avg_item_conf = float(sum(item_scores) / len(item_scores)) if item_scores else 0.0
        final_score = round(avg_item_conf, 2)

        if final_score < self.low_conf_threshold:
            warnings.append("Low confidence line items")

        return final_score, warnings

    def compute_all(self, extracted_data):
        store = extracted_data.get("store_name", {})
        date = extracted_data.get("date", {})
        items = extracted_data.get("items", [])
        total = extracted_data.get("total_amount", {})

        store_conf, store_warn = self.score_store_name(store)
        date_conf, date_warn = self.score_date(date)
        total_conf, total_warn = self.score_total_amount(total, items)
        items_conf, items_warn = self.score_items(items)

        overall_warnings = store_warn + date_warn + total_warn + items_warn

        formatted_items = []
        for it in items:
            formatted_items.append({
                "name": it["name"]["value"],
                "price": it["price"]["value"]
            })

        structured_output = {
            "store_name": store.get("value", "UNKNOWN"),
            "date": date.get("value", "UNKNOWN"),
            "items": formatted_items,
            "total_amount": total.get("value", "0.00")
        }

        confidence_output = {
            "store_name": {
                "value": store.get("value", "UNKNOWN"),
                "confidence": store_conf,
                "low_confidence": store_conf < self.low_conf_threshold
            },
            "date": {
                "value": date.get("value", "UNKNOWN"),
                "confidence": date_conf,
                "low_confidence": date_conf < self.low_conf_threshold
            },
            "items": {
                "value": formatted_items,
                "confidence": items_conf,
                "low_confidence": items_conf < self.low_conf_threshold
            },
            "total_amount": {
                "value": total.get("value", "0.00"),
                "confidence": total_conf,
                "low_confidence": total_conf < self.low_conf_threshold
            },
            "overall_reliability": {
                "average_confidence": round(float((store_conf + date_conf + total_conf + items_conf) / 4.0), 2),
                "is_reliable": len(overall_warnings) == 0 and (store_conf + date_conf + total_conf) / 3.0 >= self.low_conf_threshold,
                "warnings": list(set(overall_warnings))
            }
        }

        return structured_output, confidence_output
