import json
import os
import time

class IAPManager:
    def __init__(self, storage_path=None):
        self.storage_path = storage_path or os.path.join(
            os.path.expanduser("~"), "Documents", "LP_PC_Suite", "iap_transactions.json"
        )
        self.transactions = self._load_transactions()
        self.auto_repeat_enabled = False
        self.save_for_restore_enabled = False

    def _load_transactions(self):
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def _save_transactions(self):
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        with open(self.storage_path, 'w', encoding='utf-8') as f:
            json.dump(self.transactions, f, indent=2, ensure_ascii=False)

    def save_purchase(self, package_name, product_id, purchase_data):
        transaction = {
            'id': len(self.transactions) + 1,
            'package': package_name,
            'product': product_id,
            'data': purchase_data,
            'timestamp': time.time()
        }
        self.transactions.append(transaction)
        self._save_transactions()
        print(f"[IAPManager] Saved purchase: {product_id} in {package_name}")
        return transaction['id']

    def get_saved_purchases(self, package_name=None):
        if package_name:
            return [t for t in self.transactions if t['package'] == package_name]
        return self.transactions

    def auto_repeat(self, package_name, product_id):
        for t in self.transactions:
            if t['package'] == package_name and t['product'] == product_id:
                fake_response = {
                    "code": 0,
                    "message": "Success (auto-repeat)",
                    "purchaseData": json.dumps(t['data']),
                    "signature": "LP-PC-Suite-AutoRepeat"
                }
                print(f"[IAPManager] Auto-repeated purchase: {product_id}")
                return fake_response
        print(f"[IAPManager] No saved purchase found for {product_id}")
        return None

    def delete_purchase(self, transaction_id):
        self.transactions = [t for t in self.transactions if t['id'] != transaction_id]
        self._save_transactions()
        print(f"[IAPManager] Deleted purchase ID: {transaction_id}")

    def clear_all(self):
        self.transactions = []
        self._save_transactions()
        print("[IAPManager] All purchases cleared")