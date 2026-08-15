import json
import time
import random
import base64
import hashlib
from http.server import HTTPServer, BaseHTTPRequestHandler
from patcher.iap_manager import IAPManager

class IAPProxyHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        try:
            request = json.loads(post_data.decode('utf-8'))
        except Exception:
            request = {}

        method = request.get('method', self.path.strip('/'))
        package_name = request.get('packageName', 'com.example.app')
        product_id = request.get('productId', 'product')
        print(f"[*] [Proxy] Received {method} for {package_name}:{product_id}")

        if method == 'getBuyIntent' or 'buy' in self.path:
            response = self._get_buy_intent_response(package_name, product_id, request)
        elif method == 'getPurchases' or 'purchases' in self.path:
            response = self._get_purchases_response(package_name)
        elif method == 'isBillingSupported' or 'supported' in self.path:
            response = self._is_billing_supported_response()
        elif method == 'consumePurchase' or 'consume' in self.path:
            response = self._consume_purchase_response()
        else:
            response = {"code": 0, "message": "Success"}

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())

    def _get_buy_intent_response(self, package_name, product_id, request):
        order_id = f"GPA.{random.randint(1000,9999)}-{random.randint(1000,9999)}-{random.randint(10000,99999)}"
        purchase_token = base64.b64encode(
            f"{package_name}:{product_id}:{order_id}:{int(time.time()*1000)}".encode()
        ).decode()
        purchase_data = {
            "orderId": order_id,
            "packageName": package_name,
            "productId": product_id,
            "purchaseTime": int(time.time() * 1000),
            "purchaseState": 0,
            "purchaseToken": purchase_token,
            "autoRenewing": False,
            "developerPayload": request.get('developerPayload', '')
        }
        signature = base64.b64encode(
            hashlib.sha1(json.dumps(purchase_data).encode()).digest()
        ).decode()

        # Tích hợp IAPManager: lưu giao dịch nếu bật
        manager = IAPManager()
        if manager.save_for_restore_enabled:
            manager.save_purchase(package_name, product_id, purchase_data)
            print(f"[*] [Proxy] Purchase saved via IAPManager")

        # Nếu auto-repeat được bật, có thể trả về giao dịch đã lưu thay vì tạo mới
        if manager.auto_repeat_enabled:
            repeated = manager.auto_repeat(package_name, product_id)
            if repeated:
                return repeated

        return {
            "code": 0,
            "message": "Success",
            "purchaseData": json.dumps(purchase_data),
            "signature": signature
        }

    def _get_purchases_response(self, package_name):
        return {"code": 0, "purchases": [], "message": "Success"}

    def _is_billing_supported_response(self):
        return {"code": 0, "message": "Billing supported"}

    def _consume_purchase_response(self):
        return {"code": 0, "message": "Purchase consumed"}

class IAPProxyServer:
    def __init__(self, host='localhost', port=8888):
        self.host = host
        self.port = port
        self.server = None

    def start(self):
        self.server = HTTPServer((self.host, self.port), IAPProxyHandler)
        print(f"[*] [ProxyServer] Running on {self.host}:{self.port}")
        self.server.serve_forever()

    def stop(self):
        if self.server:
            self.server.shutdown()