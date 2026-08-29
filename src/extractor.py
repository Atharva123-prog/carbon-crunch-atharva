import re

KNOWN_VENDORS = [
    "WALMART", "WAL-MART", "TARGET", "COSTCO", "ALDI", "KROGER", "STARBUCKS",
    "7-ELEVEN", "SEVEN ELEVEN", "MCDONALD'S", "MCDONALDS", "HOME DEPOT",
    "BEST BUY", "CVS", "WALGREENS", "TESCO", "CARREFOUR", "SUBWAY", "BURGER KING",
    "PUBLIX", "SAFEWAY", "WHOLE FOODS", "TRADER JOE'S", "TRADER JOES", "DUNKIN"
]

IGNORE_HEADER_KEYWORDS = [
    "RECEIPT", "TAX INVOICE", "INVOICE", "WELCOME", "THANK YOU", "TEL", "FAX",
    "PHONE", "DATE", "TIME", "CASHIER", "STORE #", "REG #", "TRANS #", "SLIP #"
]

SUMMARY_KEYWORDS = [
    "SUBTOTAL", "SUB TOTAL", "TAX", "VAT", "GST", "TOTAL", "GRAND TOTAL",
    "AMOUNT DUE", "BALANCE DUE", "CHANGE", "CASH", "CARD", "DEBIT", "CREDIT",
    "SAVINGS", "BALANCE", "ITEMS SOLD", "PAYMENT", "VISA", "MASTERCARD", "AMEX"
]

class KeyInfoExtractor:
    def __init__(self):
        pass

    def extract_store_name(self, lines, image_height=1000):
        if not lines:
            return {"value": "UNKNOWN", "confidence": 0.0, "source": "none"}

        header_lines = [l for l in lines if l["bbox"][1] < image_height * 0.4]
        if not header_lines:
            header_lines = lines[:5]

        for line in header_lines:
            txt_upper = line["text"].upper()
            for vendor in KNOWN_VENDORS:
                if vendor in txt_upper:
                    return {
                        "value": vendor,
                        "confidence": max(0.92, line["confidence"]),
                        "source": "dictionary_match"
                    }

        candidates = []
        for line in header_lines:
            txt = line["text"].strip()
            txt_upper = txt.upper()

            if len(txt) < 3 or re.match(r'^[\d\s\-\.\:\/\#\$\,]+$', txt):
                continue
            if any(kw in txt_upper for kw in IGNORE_HEADER_KEYWORDS):
                continue

            candidates.append(line)

        if candidates:
            best_candidate = max(candidates, key=lambda c: (c["bbox"][3], c["confidence"]))
            clean_val = re.sub(r'[^a-zA-Z0-9\s\&\.\-]', '', best_candidate["text"]).strip()
            return {
                "value": clean_val if clean_val else best_candidate["text"],
                "confidence": min(0.85, best_candidate["confidence"]),
                "source": "heuristic_header"
            }

        return {"value": "UNKNOWN", "confidence": 0.0, "source": "fallback"}

    def extract_date(self, lines):
        if not lines:
            return {"value": "UNKNOWN", "confidence": 0.0, "source": "none"}

        date_patterns = [
            (r'\b(20\d{2}[-\/\.](?:0[1-9]|1[0-2])[-\/\.](?:0[1-9]|[12]\d|3[01]))\b', '%Y-%m-%d'),
            (r'\b((?:0[1-9]|1[0-2])[-\/\.](?:0[1-9]|[12]\d|3[01])[-\/\.]20\d{2})\b', '%m/%d/%Y'),
            (r'\b((?:0[1-9]|[12]\d|3[01])[-\/\.](?:0[1-9]|1[0-2])[-\/\.]20\d{2})\b', '%d/%m/%Y'),
            (r'\b((?:0[1-9]|1[0-2])[-\/\.](?:0[1-9]|[12]\d|3[01])[-\/\.]\d{2})\b', '%m/%d/%y'),
            (r'\b((?:0[1-9]|[12]\d|3[01])\s+(?:JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)[a-z]*\s+20\d{2})\b', '%d %b %Y'),
            (r'\b((?:JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)[a-z]*\s+(?:0[1-9]|[12]\d|3[01])\,?\s+20\d{2})\b', '%b %d %Y')
        ]

        matches = []
        for idx, line in enumerate(lines):
            txt = line["text"]
            txt_upper = txt.upper()
            has_date_kw = any(kw in txt_upper for kw in ["DATE", "TIME", "TRAN", "SOLD"])

            for pattern, fmt in date_patterns:
                found = re.findall(pattern, txt, re.IGNORECASE)
                for d_str in found:
                    conf = min(0.98, line["confidence"] + (0.15 if has_date_kw else 0.0))
                    matches.append({
                        "value": d_str,
                        "confidence": float(conf),
                        "line_idx": idx,
                        "has_kw": has_date_kw
                    })

        if matches:
            best_match = max(matches, key=lambda m: (m["has_kw"], m["confidence"]))
            return {
                "value": best_match["value"],
                "confidence": round(best_match["confidence"], 2),
                "source": "regex_pattern"
            }

        return {"value": "UNKNOWN", "confidence": 0.0, "source": "fallback"}

    def extract_items(self, lines, image_height=1000):
        if not lines:
            return []

        price_pattern = r'(\$?\s*\d+\.\d{2})'
        items = []

        for line in lines:
            txt = line["text"].strip()
            txt_upper = txt.upper()

            if any(kw in txt_upper for kw in SUMMARY_KEYWORDS):
                continue
            if line["bbox"][1] < image_height * 0.15 or line["bbox"][1] > image_height * 0.85:
                continue

            price_matches = re.findall(price_pattern, txt)
            if price_matches:
                item_price = price_matches[-1].replace('$', '').strip()
                item_name = re.sub(price_pattern, '', txt).strip()
                item_name = re.sub(r'^\d+\s*x?\s*', '', item_name).strip()
                item_name = re.sub(r'[^a-zA-Z0-9\s\&\.\-]', '', item_name).strip()

                if len(item_name) >= 2 and not item_name.isdigit():
                    try:
                        p_val = float(item_price)
                        if 0.01 <= p_val <= 500.0:
                            items.append({
                                "name": {"value": item_name, "confidence": round(float(line["confidence"]), 2)},
                                "price": {"value": f"{p_val:.2f}", "confidence": round(float(line["confidence"]), 2)}
                            })
                    except ValueError:
                        continue

        return items

    def extract_total_amount(self, lines, items=None, image_height=1000):
        if not lines:
            return {"value": "0.00", "confidence": 0.0, "source": "none"}

        total_keywords = [
            "GRAND TOTAL", "TOTAL AMOUNT", "TOTAL DUE", "AMOUNT DUE",
            "TOTAL CASH", "NET TOTAL", "BALANCE DUE", "TOTAL"
        ]
        exclude_keywords = ["SUBTOTAL", "SUB TOTAL", "TAX", "CHANGE", "CASH", "SAVINGS"]

        price_pattern = r'(\$?\s*\d+\.\d{2})'
        candidates = []

        for idx, line in enumerate(lines):
            txt = line["text"].strip()
            txt_upper = txt.upper()

            if any(ex in txt_upper for ex in exclude_keywords) and "GRAND" not in txt_upper:
                continue

            for kw in total_keywords:
                if kw in txt_upper:
                    prices = re.findall(price_pattern, txt)
                    if prices:
                        p_val = float(prices[-1].replace('$', '').strip())
                        candidates.append({
                            "value": f"{p_val:.2f}",
                            "confidence": min(0.98, line["confidence"] + 0.1),
                            "priority": 2 if kw != "TOTAL" else 1,
                            "line_y": line["bbox"][1]
                        })
                    else:
                        if idx + 1 < len(lines):
                            next_line = lines[idx + 1]
                            next_prices = re.findall(price_pattern, next_line["text"])
                            if next_prices:
                                p_val = float(next_prices[-1].replace('$', '').strip())
                                candidates.append({
                                    "value": f"{p_val:.2f}",
                                    "confidence": min(0.95, next_line["confidence"]),
                                    "priority": 2 if kw != "TOTAL" else 1,
                                    "line_y": next_line["bbox"][1]
                                })

        if candidates:
            best_cand = max(candidates, key=lambda c: (c["priority"], c["confidence"], c["line_y"]))
            return {
                "value": best_cand["value"],
                "confidence": round(best_cand["confidence"], 2),
                "source": "keyword_anchor"
            }

        all_prices = []
        for line in lines:
            if line["bbox"][1] > image_height * 0.4:
                txt = line["text"]
                for p_str in re.findall(price_pattern, txt):
                    try:
                        val = float(p_str.replace('$', '').strip())
                        all_prices.append((val, line["confidence"]))
                    except ValueError:
                        continue

        if all_prices:
            max_price, conf = max(all_prices, key=lambda x: x[0])
            return {
                "value": f"{max_price:.2f}",
                "confidence": round(min(0.75, conf), 2),
                "source": "max_monetary_fallback"
            }

        if items:
            item_sum = sum(float(it["price"]["value"]) for it in items if "price" in it)
            if item_sum > 0:
                return {
                    "value": f"{item_sum:.2f}",
                    "confidence": 0.65,
                    "source": "item_sum_fallback"
                }

        return {"value": "0.00", "confidence": 0.0, "source": "fallback"}

    def extract_all(self, ocr_result, image_shape=(1000, 1000)):
        lines = ocr_result.get("lines", [])
        img_height = image_shape[0]

        store = self.extract_store_name(lines, img_height)
        date = self.extract_date(lines)
        items = self.extract_items(lines, img_height)
        total = self.extract_total_amount(lines, items, img_height)

        return {
            "store_name": store,
            "date": date,
            "items": items,
            "total_amount": total
        }
