"""
WebSocket endpoints for real-time chat.
"""
import jwt
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from sqlmodel import Session

from app.core import security
from app.core.config import settings
from app.core.db import engine
from app.models import User, TokenPayload
from app.websocket import manager

router = APIRouter(tags=["websocket"])


async def get_user_from_token(token: str) -> User | None:
    """Validate token and return user."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[security.ALGORITHM])
        token_data = TokenPayload(**payload)
        
        with Session(engine) as session:
            user = session.get(User, token_data.sub)
            if user and user.is_active:
                return user
    except Exception:
        pass
    return None


@router.websocket("/ws/user")
async def websocket_user_endpoint(
    websocket: WebSocket,
    token: str = Query(...),
):
    """WebSocket endpoint for regular users."""
    user = await get_user_from_token(token)
    if not user:
        await websocket.close(code=4001, reason="Unauthorized")
        return
    
    user_id = str(user.id)
    await manager.connect_user(websocket, user_id)
    
    try:
        while True:
            # Receive messages from user (for heartbeat/ping)
            data = await websocket.receive_json()
            
            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
            elif data.get("type") == "typing":
                # Broadcast typing indicator to admin
                # Get active chat and notify assigned admin
                from app import crud
                with Session(engine) as session:
                    chat = crud.get_active_or_pending_chat_by_user(
                        session=session, user_id=user.id
                    )
                    if chat and chat.admin_id:
                        await manager.send_to_admin(str(chat.admin_id), {
                            "type": "user_typing",
                            "chat_id": str(chat.id),
                            "user_id": user_id,
                        })
    except WebSocketDisconnect:
        manager.disconnect_user(websocket, user_id)
    except Exception:
        manager.disconnect_user(websocket, user_id)


@router.websocket("/ws/admin")
async def websocket_admin_endpoint(
    websocket: WebSocket,
    token: str = Query(...),
):
    """WebSocket endpoint for admins."""
    user = await get_user_from_token(token)
    if not user or (not user.is_superuser and not user.is_admin()):
        await websocket.close(code=4001, reason="Unauthorized")
        return
    
    admin_id = str(user.id)
    await manager.connect_admin(websocket, admin_id)
    
    try:
        while True:
            data = await websocket.receive_json()
            
            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
            elif data.get("type") == "typing":
                # Broadcast typing to specific user
                chat_id = data.get("chat_id")
                user_id = data.get("user_id")
                if user_id:
                    await manager.send_to_user(user_id, {
                        "type": "admin_typing",
                        "chat_id": chat_id,
                    })
            elif data.get("type") == "get_online_users":
                # Return list of online users
                online_users = manager.get_online_users()
                await websocket.send_json({
                    "type": "online_users",
                    "users": online_users,
                })
    except WebSocketDisconnect:
        manager.disconnect_admin(websocket, admin_id)
    except Exception:
        manager.disconnect_admin(websocket, admin_id)
