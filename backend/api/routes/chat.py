"""backend/api/routes/chat.py — Chat API endpoints"""

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlmodel import Session, select
import json

from backend.db.session import get_session
from backend.models.conversation import Conversation, Message
from backend.api.schemas import ChatRequest, ChatResponse, ConversationResponse, MessageResponse
from backend.services.agent_service import run_chat_stream

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.websocket("/ws")
async def chat_websocket(websocket: WebSocket, db: Session = Depends(get_session)):
    """WebSocket endpoint for streaming chat responses."""
    await websocket.accept()
    try:
        # Receive the first configuration/start message
        data = await websocket.receive_text()
        req_data = json.loads(data)
        
        message = req_data.get("message", "")
        conversation_id = req_data.get("conversation_id")
        customer_email = req_data.get("customer_email")
        images = req_data.get("images", [])

        if conversation_id:
            conversation = db.get(Conversation, conversation_id)
            if not conversation:
                await websocket.send_text(json.dumps({"type": "error", "content": "Conversation not found."}))
                await websocket.close()
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
        except:
            pass


@router.get("/conversations", response_model=list[ConversationResponse])
def list_conversations(
    email: str | None = None,
    status: str = "all",
    limit: int = 50,
    db: Session = Depends(get_session),
):
    """List recent conversations, optionally filtered by user email."""
    query = select(Conversation).order_by(Conversation.started_at.desc()).limit(limit)
    if email:
        query = query.where(Conversation.customer_email.ilike(email))
    if status != "all":
        query = query.where(Conversation.status == status)
    conversations = db.exec(query).all()
    return conversations


@router.get("/conversations/{conversation_id}/messages", response_model=list[MessageResponse])
def get_messages(conversation_id: str, db: Session = Depends(get_session)):
    """Get all messages in a conversation."""
    conv = db.get(Conversation, conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found.")

    messages = db.exec(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
    ).all()
    return messages


@router.delete("/conversations/{conversation_id}")
def delete_conversation(conversation_id: str, db: Session = Depends(get_session)):
    """Delete a conversation and all associated messages."""
    conv = db.get(Conversation, conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found.")

    # Delete messages
    msgs = db.exec(select(Message).where(Message.conversation_id == conversation_id)).all()
    for m in msgs:
        db.delete(m)
    db.delete(conv)
    db.commit()
    return {"status": "ok", "message": f"Conversation {conversation_id} deleted."}


@router.patch("/conversations/{conversation_id}")
def update_conversation(conversation_id: str, summary: str, db: Session = Depends(get_session)):
    """Rename/update conversation title summary."""
    conv = db.get(Conversation, conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found.")

    conv.summary = summary
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv
