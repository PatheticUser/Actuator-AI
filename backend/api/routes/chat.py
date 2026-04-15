"""backend/api/routes/chat.py — Chat API endpoints"""

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from backend.db.session import get_session
from backend.models.conversation import Conversation, Message
from backend.api.schemas import ChatRequest, ChatResponse, ConversationResponse, MessageResponse
from backend.services.agent_service import run_chat

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/", response_model=ChatResponse)
async def send_message(request: ChatRequest, db: Session = Depends(get_session)):
    """Send message to Actuator AI. Routes through Supervisor to specialist agents."""

    # Create or get conversation
    if request.conversation_id:
        conversation = db.get(Conversation, request.conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail=f"Conversation {request.conversation_id} not found.")
        conv_id = conversation.id
    else:
        conversation = Conversation(customer_email=request.customer_email)
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        conv_id = conversation.id

    # Run through agent pipeline
    result = await run_chat(
        message=request.message,
        conversation_id=conv_id,
        db=db,
        customer_email=request.customer_email,
    )

    return ChatResponse(
        conversation_id=conv_id,
        response=result["response"],
        agent_name=result["agent_name"],
        needs_approval=result["needs_approval"],
        approval_items=result["approval_items"],
    )


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
