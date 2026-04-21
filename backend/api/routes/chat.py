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

        if conversation_id:
            conversation = db.get(Conversation, conversation_id)
            if not conversation:
                await websocket.send_text(json.dumps({"type": "error", "content": "Conversation not found."}))
                await websocket.close()
                return
            conv_id = conversation.id
        else:
            conversation = Conversation(customer_email=customer_email)
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
    status: str = "all",
    limit: int = 20,
    db: Session = Depends(get_session),
):
    """List recent conversations."""
    query = select(Conversation).order_by(Conversation.started_at.desc()).limit(limit)
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
