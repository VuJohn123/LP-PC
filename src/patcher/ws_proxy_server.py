import asyncio
import json
import time
import random
import base64
import hashlib
from websockets.server import serve

class WSBillingProxy:
    """WebSocket Proxy Server mô phỏng Google Play Billing Service."""
    def __init__(self, host='0.0.0.0', port=8888):
        self.host = host
        self.port = port
        self.server = None

    async def handle_client(self, websocket):
        print(f"[*] [WSProxy] Client connected: {websocket.remote_address}")
        try:
            async for message in websocket:
                await self.process_message(websocket, message)
        except Exception as e:
            print(f"[!] [WSProxy] Connection error: {e}")

    async def process_message(self, websocket, message):
        try:
            request = json.loads(message)
        except json.JSONDecodeError:
            await websocket.send(json.dumps({"error": "Invalid JSON"}))
            return

        method = request.get('method', '')
        package_name = request.get('packageName', 'com.example.app')
        product_id = request.get('productId', 'product')
        print(f"[*] [WSProxy] Received {method} for {package_name}:{product_id}")

        if method == 'getBuyIntent':
            response = self._get_buy_intent_response(package_name, product_id, request)
        elif method == 'getPurchases':
            response = self._get_purchases_response(package_name)
        elif method == 'isBillingSupported':
            response = self._is_billing_supported_response()
        elif method == 'consumePurchase':
            response = self._consume_purchase_response(request)
        else:
            response = {"code": 0, "message": "Unknown method"}

        await websocket.send(json.dumps(response))

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

    def _consume_purchase_response(self, request):
        return {"code": 0, "message": "Purchase consumed"}

    async def start(self):
        print(f"[*] [WSProxy] Starting WebSocket server on {self.host}:{self.port}")
        self.server = await serve(self.handle_client, self.host, self.port, ping_interval=30, ping_timeout=10)
        await self.server.wait_closed()

    def stop(self):
        if self.server:
            self.server.close()