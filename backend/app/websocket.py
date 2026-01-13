"""
WebSocket connection manager for real-time chat functionality.
"""
import json
import uuid
from typing import Any
from datetime import datetime

from fastapi import WebSocket


class ConnectionManager:
    """Manages WebSocket connections for real-time chat."""
    
    def __init__(self):
        # Map user_id to their WebSocket connections (support multiple tabs)
        self.active_connections: dict[str, list[WebSocket]] = {}
        # Map admin_id to their WebSocket connections
        self.admin_connections: dict[str, list[WebSocket]] = {}
    
    async def connect_user(self, websocket: WebSocket, user_id: str) -> None:
        """Connect a user to WebSocket."""
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
    
    async def connect_admin(self, websocket: WebSocket, admin_id: str) -> None:
        """Connect an admin to WebSocket."""
        await websocket.accept()
        if admin_id not in self.admin_connections:
            self.admin_connections[admin_id] = []
        self.admin_connections[admin_id].append(websocket)
    
    def disconnect_user(self, websocket: WebSocket, user_id: str) -> None:
        """Disconnect a user's WebSocket."""
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
    
    def disconnect_admin(self, websocket: WebSocket, admin_id: str) -> None:
        """Disconnect an admin's WebSocket."""
        if admin_id in self.admin_connections:
            if websocket in self.admin_connections[admin_id]:
                self.admin_connections[admin_id].remove(websocket)
            if not self.admin_connections[admin_id]:
                del self.admin_connections[admin_id]
    
    async def send_to_user(self, user_id: str, message: dict[str, Any]) -> None:
        """Send message to a specific user."""
        if user_id in self.active_connections:
            message_json = json.dumps(message, default=str)
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_text(message_json)
                except Exception:
                    pass
    
    async def send_to_admin(self, admin_id: str, message: dict[str, Any]) -> None:
        """Send message to a specific admin."""
        if admin_id in self.admin_connections:
            message_json = json.dumps(message, default=str)
            for connection in self.admin_connections[admin_id]:
                try:
                    await connection.send_text(message_json)
                except Exception:
                    pass
    
    async def broadcast_to_admins(self, message: dict[str, Any]) -> None:
        """Broadcast message to all connected admins."""
        message_json = json.dumps(message, default=str)
        for admin_id, connections in self.admin_connections.items():
            for connection in connections:
                try:
                    await connection.send_text(message_json)
                except Exception:
                    pass
    
    def is_user_online(self, user_id: str) -> bool:
        """Check if a user is currently online."""
        return user_id in self.active_connections and len(self.active_connections[user_id]) > 0
    
    def is_admin_online(self, admin_id: str) -> bool:
        """Check if an admin is currently online."""
        return admin_id in self.admin_connections and len(self.admin_connections[admin_id]) > 0
    
    def get_online_admins(self) -> list[str]:
        """Get list of online admin IDs."""
        return list(self.admin_connections.keys())
    
    def get_online_users(self) -> list[str]:
        """Get list of online user IDs."""
        return list(self.active_connections.keys())


# Global connection manager instance
manager = ConnectionManager()
