"""backend/api/routes/chat.py — Chat API endpoints"""

import json
import jwt
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlmodel import Session, select

from backend.core.config import settings
from backend.db.session import get_session
from backend.models.conversation import Conversation, Message
from backend.api.schemas import ConversationResponse, MessageResponse
from backend.api.routes.auth import get_user_email_from_token
from backend.services.agent_service import run_chat_stream

router = APIRouter(prefix="/chat", tags=["Chat"])

_MAX_MESSAGE_LENGTH = 12_000
_MAX_IMAGES = 4
_MAX_IMAGE_PAYLOAD_LENGTH = 8_000_000


@router.websocket("/ws")
async def chat_websocket(websocket: WebSocket, db: Session = Depends(get_session)):
    """WebSocket endpoint for streaming chat responses.

    Auth model:
      - A valid JWT is REQUIRED (sent in the first message body or as
        ?token= query param). Cross-site WebSocket hijacking is prevented
        both by the origin check and by requiring authentication.
      - The token subject is the authoritative customer_email.
    """
    # CORSMiddleware never runs for WebSocket connections, so enforce the
    # allowed-origin list here to prevent cross-site WebSocket hijacking.
    # is_allowed_origin() also trusts loopback origins so the local Vite dev
    # server (proxied to this backend) can connect.
    origin = websocket.headers.get("origin")
    if not settings.is_allowed_origin(origin):
        print(f"WebSocket rejected: origin {origin!r} not in CORS_ORIGINS")
        await websocket.close(code=1008)  # policy violation
        return

    # Token may arrive as a query param or inside the first frame.
    token = websocket.query_params.get("token") or ""

    await websocket.accept()
    try:
        # Receive the first configuration/start message
        data = await websocket.receive_text()
        req_data = json.loads(data)
        token = req_data.get("token") or token

        if not token:
            await websocket.send_text(json.dumps({
                "type": "error",
                "content": "Authentication required.",
            }))
            await websocket.close(code=1008)
            return

        # Verify JWT; invalid/expired tokens must never impersonate an email.
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            customer_email = payload.get("sub") or ""
        except jwt.PyJWTError:
            await websocket.send_text(json.dumps({
                "type": "error",
                "content": "Invalid or expired session. Please log in again.",
            }))
            await websocket.close(code=1008)
            return

        message = req_data.get("message", "")
        conversation_id = req_data.get("conversation_id")
        images = req_data.get("images", [])
        if not isinstance(message, str) or len(message) > _MAX_MESSAGE_LENGTH:
            await websocket.send_text(json.dumps({
                "type": "error",
                "content": "Message is too large. Keep messages under 12,000 characters.",
            }))
            await websocket.close(code=1009)
            return
        if not isinstance(images, list) or len(images) > _MAX_IMAGES or any(
            not isinstance(image, str) or len(image) > _MAX_IMAGE_PAYLOAD_LENGTH
            for image in images
        ):
            await websocket.send_text(json.dumps({
                "type": "error",
                "content": "Attachments exceed the supported limit.",
            }))
            await websocket.close(code=1009)
            return

        if conversation_id:
            conversation = db.get(Conversation, conversation_id)
            # Ownership check: never stream into another user's conversation.
            if not conversation:
                await websocket.send_text(json.dumps({"type": "error", "content": "Conversation not found."}))
                await websocket.close()
                return
            if conversation.customer_email and conversation.customer_email != customer_email:
                await websocket.send_text(json.dumps({"type": "error", "content": "Not your conversation."}))
                await websocket.close(code=1008)
                return
            conv_id = conversation.id
        else:
            summary_text = message[:30] + '...' if len(message) > 30 else message
            conversation = Conversation(customer_email=customer_email, summary=summary_text)
            db.add(conversation)
            db.commit()
            db.refresh(conversation)
            conv_id = conversation.id

        # Send back conversation_id so frontend can store it
        await websocket.send_text(json.dumps({
            "type": "conv_id",
            "conversation_id": conv_id
        }))

        # stream from backend service
        async for chunk in run_chat_stream(
            message=message,
            conversation_id=conv_id,
            db=db,
            customer_email=customer_email,
            images=images,
        ):
            await websocket.send_text(chunk)

    except WebSocketDisconnect:
        print("WebSocket client disconnected.")
    except Exception as e:
        print(f"WebSocket Error: {e}")
        try:
            await websocket.close()
        except Exception:
            pass


@router.get("/conversations", response_model=list[ConversationResponse])
def list_conversations(
    email: str | None = None,
    status: str = "all",
    limit: int = 50,
    token_email: str = Depends(get_user_email_from_token),
    db: Session = Depends(get_session),
):
    """List recent conversations for the authenticated user.

    The email query param is honored only if it matches the JWT subject —
    callers can never enumerate other users' conversations.
    """
    if email and email != token_email:
        raise HTTPException(status_code=403, detail="Cannot read other users' conversations.")
    query = (
        select(Conversation)
        .where(Conversation.customer_email == token_email)
        .order_by(Conversation.started_at.desc())
        .limit(limit)
    )
    if status != "all":
        query = query.where(Conversation.status == status)
    conversations = db.exec(query).all()
    return conversations


@router.get("/conversations/{conversation_id}/messages", response_model=list[MessageResponse])
def get_messages(
    conversation_id: str,
    token_email: str = Depends(get_user_email_from_token),
    db: Session = Depends(get_session),
):
    """Get all messages in a conversation owned by the authenticated user."""
    conv = db.get(Conversation, conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    if conv.customer_email and conv.customer_email != token_email:
        raise HTTPException(status_code=403, detail="Not your conversation.")

    messages = db.exec(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
    ).all()
    return messages


@router.delete("/conversations/{conversation_id}")
def delete_conversation(
    conversation_id: str,
    token_email: str = Depends(get_user_email_from_token),
    db: Session = Depends(get_session),
):
    """Delete a conversation and all associated messages (owner only)."""
    conv = db.get(Conversation, conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    if conv.customer_email and conv.customer_email != token_email:
        raise HTTPException(status_code=403, detail="Not your conversation.")

    # Delete messages
    msgs = db.exec(select(Message).where(Message.conversation_id == conversation_id)).all()
    for m in msgs:
        db.delete(m)
    db.delete(conv)
    db.commit()
    return {"status": "ok", "message": f"Conversation {conversation_id} deleted."}


@router.patch("/conversations/{conversation_id}")
def update_conversation(
    conversation_id: str,
    summary: str,
    token_email: str = Depends(get_user_email_from_token),
    db: Session = Depends(get_session),
):
    """Rename/update conversation title summary (owner only)."""
    conv = db.get(Conversation, conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    if conv.customer_email and conv.customer_email != token_email:
        raise HTTPException(status_code=403, detail="Not your conversation.")

    conv.summary = summary
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv
