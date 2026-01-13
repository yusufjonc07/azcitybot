"""
Chat-related API routes for the web dashboard.
"""
import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query
from sqlmodel import Session, select, func, desc

from app.api.deps import (
    CurrentUser,
    SessionDep,
    get_db,
)
from app.models import (
    User, UserStatus, UserPublic,
    SupportChat, SupportChatCreate, SupportChatUpdate, ChatStatus,
)
from app.chat_models import (
    WebMessage, WebMessageCreate, WebMessagePublic, WebMessagesPublic,
    WebMessageType, SupportChatWithUser, SupportChatsWithUsersPublic,
)
from app.websocket import manager
from app import crud

router = APIRouter(prefix="/chat", tags=["chat"])


# =============================================================================
# Helper Functions
# =============================================================================

def get_support_chat_with_user(session: Session, chat: SupportChat) -> SupportChatWithUser:
    """Convert SupportChat to SupportChatWithUser with user info."""
    user = session.get(User, chat.user_id)
    
    # Get last message
    last_msg_stmt = select(WebMessage).where(
        WebMessage.support_chat_id == chat.id
    ).order_by(desc(WebMessage.created_at)).limit(1)
    last_msg = session.exec(last_msg_stmt).first()
    
    # Get unread count (messages from user that admin hasn't read)
    unread_stmt = select(func.count()).select_from(WebMessage).where(
        WebMessage.support_chat_id == chat.id,
        WebMessage.is_from_user == True,
        WebMessage.is_read == False
    )
    unread_count = session.exec(unread_stmt).one()
    
    return SupportChatWithUser(
        id=chat.id,
        status=chat.status.value,
        created_at=chat.created_at,
        updated_at=chat.updated_at,
        claimed_at=chat.claimed_at,
        user_id=chat.user_id,
        admin_id=chat.admin_id,
        user_telegram_id=user.telegram_id if user else 0,
        user_full_name=user.full_name if user else None,
        user_username=user.username if user else None,
        user_photo_url=user.photo_url if user else None,
        last_message=last_msg.content if last_msg else None,
        last_message_time=last_msg.created_at if last_msg else None,
        unread_count=unread_count,
    )


# =============================================================================
# Chat Endpoints for Users (Simple Users)
# =============================================================================

@router.get("/my-status")
def get_my_chat_status(session: SessionDep, current_user: CurrentUser) -> dict[str, Any]:
    """Get current user's chat status."""
    # Check if user has pending or active chat
    chat = crud.get_active_or_pending_chat_by_user(session=session, user_id=current_user.id)
    
    if not chat:
        return {"has_chat": False, "status": None, "chat_id": None}
    
    return {
        "has_chat": True,
        "status": chat.status.value,
        "chat_id": str(chat.id),
        "admin_assigned": chat.admin_id is not None,
    }


@router.post("/start")
async def start_chat(session: SessionDep, current_user: CurrentUser) -> dict[str, Any]:
    """Start a new support chat (for users)."""
    # Check if user already has active/pending chat
    existing_chat = crud.get_active_or_pending_chat_by_user(
        session=session, user_id=current_user.id
    )
    if existing_chat:
        return {
            "chat_id": str(existing_chat.id),
            "status": existing_chat.status.value,
            "message": "You already have an active chat"
        }
    
    # Create new chat
    chat_create = SupportChatCreate(user_id=current_user.id)
    chat = crud.create_support_chat(session=session, chat_create=chat_create)
    
    # Notify all admins about new pending chat
    await manager.broadcast_to_admins({
        "type": "new_pending_chat",
        "chat": {
            "id": str(chat.id),
            "user_id": str(current_user.id),
            "user_full_name": current_user.full_name,
            "user_username": current_user.username,
            "user_photo_url": current_user.photo_url,
            "created_at": chat.created_at.isoformat(),
        }
    })
    
    return {
        "chat_id": str(chat.id),
        "status": chat.status.value,
        "message": "Chat started successfully"
    }


@router.get("/my-messages", response_model=WebMessagesPublic)
def get_my_messages(
    session: SessionDep, 
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 50
) -> WebMessagesPublic:
    """Get messages for current user's active chat."""
    chat = crud.get_active_or_pending_chat_by_user(session=session, user_id=current_user.id)
    if not chat:
        return WebMessagesPublic(data=[], count=0)
    
    # Get messages
    count_stmt = select(func.count()).select_from(WebMessage).where(
        WebMessage.support_chat_id == chat.id
    )
    count = session.exec(count_stmt).one()
    
    stmt = select(WebMessage).where(
        WebMessage.support_chat_id == chat.id
    ).order_by(WebMessage.created_at.asc()).offset(skip).limit(limit)
    messages = session.exec(stmt).all()
    
    return WebMessagesPublic(data=messages, count=count)


@router.post("/my-messages/send")
async def send_user_message(
    session: SessionDep,
    current_user: CurrentUser,
    content: str = Query(..., min_length=1, max_length=4000),
    message_type: WebMessageType = WebMessageType.text,
) -> WebMessagePublic:
    """Send a message in user's chat."""
    chat = crud.get_active_or_pending_chat_by_user(session=session, user_id=current_user.id)
    if not chat:
        raise HTTPException(status_code=404, detail="No active chat found")
    
    # Create message
    message = WebMessage(
        support_chat_id=chat.id,
        sender_id=current_user.id,
        content=content,
        message_type=message_type,
        is_from_user=True,
        is_read=False,
    )
    session.add(message)
    session.commit()
    session.refresh(message)
    
    # Notify admin if assigned
    if chat.admin_id:
        await manager.send_to_admin(str(chat.admin_id), {
            "type": "new_message",
            "chat_id": str(chat.id),
            "message": {
                "id": str(message.id),
                "content": message.content,
                "message_type": message.message_type.value,
                "is_from_user": True,
                "sender_id": str(current_user.id),
                "created_at": message.created_at.isoformat(),
            }
        })
    else:
        # Notify all admins about update to pending chat
        await manager.broadcast_to_admins({
            "type": "pending_chat_update",
            "chat_id": str(chat.id),
            "message": {
                "id": str(message.id),
                "content": message.content,
                "message_type": message.message_type.value,
                "is_from_user": True,
                "sender_id": str(current_user.id),
                "created_at": message.created_at.isoformat(),
            }
        })
    
    return message


# =============================================================================
# Chat Endpoints for Admins
# =============================================================================

def require_admin(current_user: CurrentUser) -> User:
    """Check if current user is admin."""
    if not current_user.is_superuser and not current_user.is_admin():
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


@router.get("/pending", response_model=SupportChatsWithUsersPublic)
def get_pending_chats(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 50
) -> SupportChatsWithUsersPublic:
    """Get all pending support chats (admin only)."""
    require_admin(current_user)
    
    count_stmt = select(func.count()).select_from(SupportChat).where(
        SupportChat.status == ChatStatus.pending
    )
    count = session.exec(count_stmt).one()
    
    stmt = select(SupportChat).where(
        SupportChat.status == ChatStatus.pending
    ).order_by(SupportChat.created_at.desc()).offset(skip).limit(limit)
    chats = session.exec(stmt).all()
    
    result = [get_support_chat_with_user(session, chat) for chat in chats]
    return SupportChatsWithUsersPublic(data=result, count=count)


@router.get("/active", response_model=SupportChatsWithUsersPublic)
def get_active_chats(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 50
) -> SupportChatsWithUsersPublic:
    """Get active chats assigned to current admin."""
    require_admin(current_user)
    
    count_stmt = select(func.count()).select_from(SupportChat).where(
        SupportChat.status == ChatStatus.active,
        SupportChat.admin_id == current_user.id
    )
    count = session.exec(count_stmt).one()
    
    stmt = select(SupportChat).where(
        SupportChat.status == ChatStatus.active,
        SupportChat.admin_id == current_user.id
    ).order_by(SupportChat.claimed_at.desc()).offset(skip).limit(limit)
    chats = session.exec(stmt).all()
    
    result = [get_support_chat_with_user(session, chat) for chat in chats]
    return SupportChatsWithUsersPublic(data=result, count=count)


@router.get("/all-active", response_model=SupportChatsWithUsersPublic)
def get_all_active_chats(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 50
) -> SupportChatsWithUsersPublic:
    """Get all active chats (super admin only)."""
    if not current_user.is_superuser and not current_user.is_admin(super_only=True):
        raise HTTPException(status_code=403, detail="Super admin access required")
    
    count_stmt = select(func.count()).select_from(SupportChat).where(
        SupportChat.status == ChatStatus.active
    )
    count = session.exec(count_stmt).one()
    
    stmt = select(SupportChat).where(
        SupportChat.status == ChatStatus.active
    ).order_by(SupportChat.claimed_at.desc()).offset(skip).limit(limit)
    chats = session.exec(stmt).all()
    
    result = [get_support_chat_with_user(session, chat) for chat in chats]
    return SupportChatsWithUsersPublic(data=result, count=count)


@router.post("/{chat_id}/claim")
async def claim_chat(
    chat_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> dict[str, Any]:
    """Claim a pending chat (admin only)."""
    require_admin(current_user)
    
    chat = crud.claim_support_chat(
        session=session, 
        chat_id=chat_id, 
        admin_id=current_user.id
    )
    
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found or already claimed")
    
    # Notify user that admin has joined
    await manager.send_to_user(str(chat.user_id), {
        "type": "admin_joined",
        "chat_id": str(chat.id),
        "admin_id": str(current_user.id),
        "admin_name": current_user.full_name or current_user.username,
    })
    
    # Notify other admins that chat was claimed
    await manager.broadcast_to_admins({
        "type": "chat_claimed",
        "chat_id": str(chat.id),
        "admin_id": str(current_user.id),
    })
    
    return {
        "success": True,
        "chat_id": str(chat.id),
        "status": chat.status.value,
    }


@router.post("/{chat_id}/close")
async def close_chat(
    chat_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
    cancelled: bool = False,
) -> dict[str, Any]:
    """Close a chat (admin only)."""
    require_admin(current_user)
    
    chat = crud.get_support_chat(session=session, chat_id=chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    # Only assigned admin or super admin can close
    is_super = current_user.is_superuser or current_user.is_admin(super_only=True)
    if chat.admin_id != current_user.id and not is_super:
        raise HTTPException(status_code=403, detail="Not authorized to close this chat")
    
    chat = crud.close_support_chat(session=session, chat_id=chat_id, cancelled=cancelled)
    
    # Notify user that chat is closed
    await manager.send_to_user(str(chat.user_id), {
        "type": "chat_closed",
        "chat_id": str(chat.id),
        "cancelled": cancelled,
    })
    
    return {
        "success": True,
        "chat_id": str(chat.id),
        "status": chat.status.value,
    }


@router.get("/{chat_id}/messages", response_model=WebMessagesPublic)
def get_chat_messages(
    chat_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 50,
) -> WebMessagesPublic:
    """Get messages for a specific chat (admin only)."""
    require_admin(current_user)
    
    chat = crud.get_support_chat(session=session, chat_id=chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    # Get messages
    count_stmt = select(func.count()).select_from(WebMessage).where(
        WebMessage.support_chat_id == chat_id
    )
    count = session.exec(count_stmt).one()
    
    stmt = select(WebMessage).where(
        WebMessage.support_chat_id == chat_id
    ).order_by(WebMessage.created_at.asc()).offset(skip).limit(limit)
    messages = session.exec(stmt).all()
    
    # Mark messages as read
    for msg in messages:
        if msg.is_from_user and not msg.is_read:
            msg.is_read = True
            session.add(msg)
    session.commit()
    
    return WebMessagesPublic(data=messages, count=count)


@router.post("/{chat_id}/messages/send")
async def send_admin_message(
    chat_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
    content: str = Query(..., min_length=1, max_length=4000),
    message_type: WebMessageType = WebMessageType.text,
) -> WebMessagePublic:
    """Send a message as admin."""
    require_admin(current_user)
    
    chat = crud.get_support_chat(session=session, chat_id=chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    # Only assigned admin can send messages (or claim first)
    if chat.admin_id != current_user.id:
        raise HTTPException(
            status_code=403, 
            detail="You must claim this chat first"
        )
    
    # Create message
    message = WebMessage(
        support_chat_id=chat_id,
        sender_id=current_user.id,
        content=content,
        message_type=message_type,
        is_from_user=False,
        is_read=True,  # Admin messages are marked as read
    )
    session.add(message)
    session.commit()
    session.refresh(message)
    
    # Notify user
    await manager.send_to_user(str(chat.user_id), {
        "type": "new_message",
        "chat_id": str(chat_id),
        "message": {
            "id": str(message.id),
            "content": message.content,
            "message_type": message.message_type.value,
            "is_from_user": False,
            "sender_id": str(current_user.id),
            "created_at": message.created_at.isoformat(),
        }
    })
    
    return message


@router.post("/{chat_id}/messages/read")
async def mark_messages_read(
    chat_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> dict[str, Any]:
    """Mark all messages in a chat as read."""
    require_admin(current_user)
    
    chat = crud.get_support_chat(session=session, chat_id=chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    # Update unread messages
    stmt = select(WebMessage).where(
        WebMessage.support_chat_id == chat_id,
        WebMessage.is_from_user == True,
        WebMessage.is_read == False
    )
    messages = session.exec(stmt).all()
    
    for msg in messages:
        msg.is_read = True
        session.add(msg)
    session.commit()
    
    # Notify user that messages were read
    await manager.send_to_user(str(chat.user_id), {
        "type": "messages_read",
        "chat_id": str(chat_id),
    })
    
    return {"success": True, "count": len(messages)}


@router.get("/{chat_id}/user", response_model=UserPublic)
def get_chat_user(
    chat_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> UserPublic:
    """Get user info for a chat."""
    require_admin(current_user)
    
    chat = crud.get_support_chat(session=session, chat_id=chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    user = session.get(User, chat.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user
