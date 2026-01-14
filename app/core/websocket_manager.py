from fastapi import WebSocket
from typing import Dict, List


class ConnectionManager:
    def __init__(self):
        # delivery_id -> sockets
        self.delivery_connections: Dict[int, List[WebSocket]] = {}

        # pharmacist_id -> sockets
        self.pharmacist_connections: Dict[int, List[WebSocket]] = {}
        
        # user_id (customer) -> sockets
        self.user_connections: Dict[int, List[WebSocket]] = {}

    # ---------------- DELIVERY ----------------
    async def connect_delivery(self, delivery_id: int, ws: WebSocket):
        await ws.accept()
        self.delivery_connections.setdefault(delivery_id, []).append(ws)

    def disconnect_delivery(self, delivery_id: int, ws: WebSocket):
        if delivery_id in self.delivery_connections:
            self.delivery_connections[delivery_id].remove(ws)
            if not self.delivery_connections[delivery_id]:
                del self.delivery_connections[delivery_id]

    async def send_delivery(self, delivery_id: int, message: dict):
        for ws in self.delivery_connections.get(delivery_id, []):
            await ws.send_json(message)

    # ---------------- PHARMACIST ----------------
    async def connect_pharmacist(self, pharmacist_id: int, ws: WebSocket):
        await ws.accept()
        self.pharmacist_connections.setdefault(pharmacist_id, []).append(ws)

    def disconnect_pharmacist(self, pharmacist_id: int, ws: WebSocket):
        if pharmacist_id in self.pharmacist_connections:
            self.pharmacist_connections[pharmacist_id].remove(ws)
            if not self.pharmacist_connections[pharmacist_id]:
                del self.pharmacist_connections[pharmacist_id]

    async def send_pharmacist(self, pharmacist_id: int, message: dict):
        for ws in self.pharmacist_connections.get(pharmacist_id, []):
            await ws.send_json(message)

    # ---------------- CUSTOMER ----------------
    async def connect_user(self, user_id: int, ws: WebSocket):
        await ws.accept()
        self.user_connections.setdefault(user_id, []).append(ws)

    def disconnect_user(self, user_id: int, ws: WebSocket):
        if user_id in self.user_connections:
            self.user_connections[user_id].remove(ws)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]

    async def send_user(self, user_id: int, message: dict):
        for ws in self.user_connections.get(user_id, []):
            await ws.send_json(message)


manager = ConnectionManager()
