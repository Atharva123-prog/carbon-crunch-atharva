import json
import os

class SummaryGenerator:
    def __init__(self):
        pass

    def generate_summary(self, receipt_results):
        total_spend = 0.0
        transaction_count = len(receipt_results)
        store_spend_map = {}
        store_count_map = {}
        item_stats_map = {}
        reliable_count = 0
        unreliable_count = 0
        transactions_detail = []
        total_items_purchased = 0

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

            if is_reliable:
                reliable_count += 1
            else:
                unreliable_count += 1

            total_spend += tot_val
            store_spend_map[store_name] = store_spend_map.get(store_name, 0.0) + tot_val
            store_count_map[store_name] = store_count_map.get(store_name, 0) + 1

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
                    receipt_item_count += 1
                    total_items_purchased += 1
                    if iname not in item_stats_map:
                        item_stats_map[iname] = {
                            "item_name": iname,
                            "quantity_purchased": 0,
                            "total_spent": 0.0
                        }
                    item_stats_map[iname]["quantity_purchased"] += 1
                    item_stats_map[iname]["total_spent"] += iprice

            transactions_detail.append({
                "receipt_id": rec.get("receipt_id", ""),
                "store_name": store_name,
                "date": date_str,
                "items_count": receipt_item_count,
                "total_amount": round(tot_val, 2),
                "is_reliable": is_reliable
            })

        avg_spend = round(total_spend / transaction_count, 2) if transaction_count > 0 else 0.0
        total_spend = round(total_spend, 2)

        spend_per_store = {}
        for sname, sspend in store_spend_map.items():
            spend_per_store[sname] = {
                "total_spend": round(sspend, 2),
                "transaction_count": store_count_map[sname],
                "average_spend": round(sspend / store_count_map[sname], 2) if store_count_map[sname] > 0 else 0.0,
                "percentage_of_total": round((sspend / total_spend * 100.0), 2) if total_spend > 0 else 0.0
            }

        purchased_items_breakdown = []
        for iname, istats in item_stats_map.items():
            qty = istats["quantity_purchased"]
            tot = round(istats["total_spent"], 2)
            avg_unit = round(tot / qty, 2) if qty > 0 else 0.0
            purchased_items_breakdown.append({
                "item_name": iname,
                "quantity_purchased": qty,
                "total_spent": tot,
                "average_unit_price": avg_unit
            })

        purchased_items_breakdown.sort(key=lambda x: x["total_spent"], reverse=True)
        highest_tx = max(transactions_detail, key=lambda x: x["total_amount"]) if transactions_detail else None

        summary_output = {
            "financial_summary": {
                "total_spend": total_spend,
                "number_of_transactions": transaction_count,
                "total_items_purchased": total_items_purchased,
                "average_transaction_spend": avg_spend,
                "highest_transaction": highest_tx,
                "spend_per_store": spend_per_store,
                "purchased_items_breakdown": purchased_items_breakdown
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
