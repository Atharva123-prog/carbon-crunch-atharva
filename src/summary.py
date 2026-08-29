import json
import os

class SummaryGenerator:
    def __init__(self):
        pass

    def generate_summary(self, receipt_results):
        total_spend = 0.0
        transaction_count = len(receipt_results)
        store_spend_map = {}
        store_items_map = {}
        store_tx_map = {}
        itemized_register = []
        reliable_count = 0
        unreliable_count = 0
        transactions_detail = []
        global_item_counter = 0

        for rec in receipt_results:
            conf_data = rec.get("confidence_output", {})

            tot_val_str = conf_data.get("total_amount", {}).get("value", "0.00")
            try:
                tot_val = float(tot_val_str)
            except ValueError:
                tot_val = 0.0

            store_name = conf_data.get("store_name", {}).get("value", "UNKNOWN")
            if not store_name:
                store_name = "UNKNOWN"

            date_str = conf_data.get("date", {}).get("value", "UNKNOWN")
            is_reliable = conf_data.get("overall_reliability", {}).get("is_reliable", False)
            receipt_id = rec.get("receipt_id", "")

            if is_reliable:
                reliable_count += 1
            else:
                unreliable_count += 1

            total_spend += tot_val
            store_spend_map[store_name] = store_spend_map.get(store_name, 0.0) + tot_val
            store_tx_map[store_name] = store_tx_map.get(store_name, 0) + 1

            items_list = conf_data.get("items", {}).get("value", [])
            receipt_item_count = 0

            for it in items_list:
                iname = it.get("name", "").strip().upper()
                iprice_str = it.get("price", "0.00")
                try:
                    iprice = float(iprice_str)
                except ValueError:
                    iprice = 0.0

                if iname and len(iname) >= 2:
                    global_item_counter += 1
                    receipt_item_count += 1
                    store_items_map[store_name] = store_items_map.get(store_name, 0) + 1

                    itemized_register.append({
                        "item_no": global_item_counter,
                        "item_name": iname,
                        "price": round(iprice, 2),
                        "store_name": store_name,
                        "date": date_str,
                        "receipt_id": receipt_id
                    })

            transactions_detail.append({
                "receipt_id": receipt_id,
                "store_name": store_name,
                "date": date_str,
                "items_count": receipt_item_count,
                "total_amount": round(tot_val, 2),
                "is_reliable": is_reliable
            })

        avg_spend = round(total_spend / transaction_count, 2) if transaction_count > 0 else 0.0
        total_spend = round(total_spend, 2)

        store_shopping_summary = []
        for sname, sspend in store_spend_map.items():
            scount = store_tx_map.get(sname, 0)
            sitems = store_items_map.get(sname, 0)
            avg_item_price = round(sspend / sitems, 2) if sitems > 0 else 0.0
            store_shopping_summary.append({
                "store_name": sname,
                "total_shopping_amount": round(sspend, 2),
                "items_purchased_count": sitems,
                "transaction_count": scount,
                "average_item_price": avg_item_price,
                "percentage_of_total": round((sspend / total_spend * 100.0), 2) if total_spend > 0 else 0.0
            })

        store_shopping_summary.sort(key=lambda x: x["total_shopping_amount"], reverse=True)
        highest_tx = max(transactions_detail, key=lambda x: x["total_amount"]) if transactions_detail else None

        summary_output = {
            "financial_summary": {
                "total_spend": total_spend,
                "number_of_transactions": transaction_count,
                "total_items_purchased": global_item_counter,
                "average_transaction_spend": avg_spend,
                "highest_transaction": highest_tx,
                "store_shopping_summary": store_shopping_summary,
                "itemized_purchase_register": itemized_register
            },
            "reliability_summary": {
                "reliable_transactions_count": reliable_count,
                "unreliable_transactions_count": unreliable_count,
                "reliability_percentage": round((reliable_count / transaction_count * 100.0), 2) if transaction_count > 0 else 0.0
            },
            "all_transactions": transactions_detail
        }
        return summary_output

    def save_summary(self, summary_output, output_path="outputs/expense_summary.json"):
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(summary_output, f, indent=2)
        return output_path
