"""
Chat API endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import StreamingResponse
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

from src.core.nlp_engine import NLPEngine, DialogueState
# from src.knowledge.rag_module import EnhancedRAG  # Temporarily disabled - requires vector store
from src.utils.logging import chat_logger as logger

router = APIRouter()

# Initialize services (in production, use dependency injection)
nlp_engine = NLPEngine()
# rag_module = EnhancedRAG()  # Temporarily disabled - requires vector store setup
rag_module = None  # Will be enabled once Pinecone is configured


class ChatMessage(BaseModel):
    """Chat message model"""
    message: str = Field(..., min_length=1, max_length=1000)
    session_id: Optional[str] = Field(default=None)
    user_id: Optional[str] = Field(default=None)
    metadata: Optional[Dict[str, Any]] = Field(default={})


class ChatResponse(BaseModel):
    """Chat response model"""
    response: str
    session_id: str
    intent: Optional[str] = None
    confidence: float
    requires_human: bool = False
    sources: Optional[list] = None
    metadata: Optional[Dict[str, Any]] = Field(default={})


class ConversationHistory(BaseModel):
    """Conversation history model"""
    session_id: str
    messages: list
    started_at: datetime
    ended_at: Optional[datetime] = None
    status: str


@router.post("/message", response_model=ChatResponse)
async def send_message(
    chat_message: ChatMessage,
    background_tasks: BackgroundTasks
) -> ChatResponse:
    """
    Process a chat message and return AI response
    """
    try:
        # Generate session ID if not provided
        session_id = chat_message.session_id or str(uuid.uuid4())
        
        # Log incoming message
        logger.info(f"Received message for session {session_id}: {chat_message.message[:50]}...")
        
        # Process message through NLP engine
        nlu_result = await nlp_engine.process_message(
            text=chat_message.message,
            session_id=session_id,
            user_id=chat_message.user_id,
            context=chat_message.metadata
        )
        
        # Get dialogue state
        dialogue_state = nlp_engine.get_dialogue_state(session_id)
        
        # Check if human handoff is needed
        if nlp_engine.dialogue_manager.should_handoff(dialogue_state):
            logger.info(f"Human handoff triggered for session {session_id}")
            return ChatResponse(
                response="I'll connect you with a human agent who can better assist you. Please wait a moment.",
                session_id=session_id,
                intent=str(nlu_result.intent.value),
                confidence=nlu_result.intent_confidence,
                requires_human=True,
                metadata={"handoff_reason": "escalation_required"}
            )
        
        # Generate response using RAG
        generation_result = await rag_module.process(
            query=chat_message.message,
            context={
                "intent": nlu_result.intent.value,
                "entities": {e.type: e.value for e in nlu_result.entities},
                "session_id": session_id,
                "turn_count": dialogue_state.turn_count
            }
        )
        
        # Log response generation
        logger.info(f"Generated response for session {session_id} with confidence {generation_result.confidence}")
        
        # Background task to save conversation
        background_tasks.add_task(
            save_conversation,
            session_id=session_id,
            user_message=chat_message.message,
            bot_response=generation_result.response,
            intent=nlu_result.intent.value,
            confidence=generation_result.confidence
        )
        
        return ChatResponse(
            response=generation_result.response,
            session_id=session_id,
            intent=nlu_result.intent.value,
            confidence=generation_result.confidence,
            requires_human=False,
            sources=generation_result.sources,
            metadata={
                "turn_count": dialogue_state.turn_count,
                "validation_passed": generation_result.validation_passed
            }
        )
        
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to process message")


@router.post("/message/stream")
async def send_message_stream(chat_message: ChatMessage):
    """
    Process a chat message and stream the response
    """
    async def generate():
        try:
            # Similar to send_message but yields chunks for streaming
            session_id = chat_message.session_id or str(uuid.uuid4())
            
            # Process NLU
            nlu_result = await nlp_engine.process_message(
                text=chat_message.message,
                session_id=session_id,
                user_id=chat_message.user_id
            )
            
            # For demo, yield response in chunks
            response = "This is a streamed response. "
            for word in response.split():
                yield f"{word} "
                
        except Exception as e:
            logger.error(f"Error in stream: {str(e)}")
            yield f"Error: {str(e)}"
    
    return StreamingResponse(generate(), media_type="text/plain")


@router.get("/session/{session_id}/history", response_model=ConversationHistory)
async def get_conversation_history(session_id: str):
    """
    Get conversation history for a session
    """
    try:
        # TODO: Implement database query
        # For now, return mock data
        return ConversationHistory(
            session_id=session_id,
            messages=[],
            started_at=datetime.now(),
            status="active"
        )
    except Exception as e:
        logger.error(f"Error fetching history: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch conversation history")


@router.post("/session/{session_id}/handoff")
async def request_human_handoff(session_id: str):
    """
    Request human agent handoff for a session
    """
    try:
        # Get dialogue state
        dialogue_state = nlp_engine.get_dialogue_state(session_id)
        if not dialogue_state:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Mark for handoff
        dialogue_state.handoff_requested = True
        
        # TODO: Implement actual handoff logic
        # - Notify human agents
        # - Transfer conversation context
        # - Update session status
        
        logger.info(f"Human handoff requested for session {session_id}")
        
        return {
            "status": "handoff_initiated",
            "session_id": session_id,
            "message": "Your conversation is being transferred to a human agent."
        }
        
    except Exception as e:
        logger.error(f"Error in handoff: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to initiate handoff")


@router.delete("/session/{session_id}")
async def end_session(session_id: str):
    """
    End a chat session
    """
    try:
        nlp_engine.clear_session(session_id)
        
        # TODO: Update session status in database
        
        logger.info(f"Session {session_id} ended")
        
        return {
            "status": "session_ended",
            "session_id": session_id
        }
        
    except Exception as e:
        logger.error(f"Error ending session: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to end session")


async def save_conversation(
    session_id: str,
    user_message: str,
    bot_response: str,
    intent: str,
    confidence: float
):
    """
    Background task to save conversation to database
    """
    try:
        # TODO: Implement database save
        logger.info(f"Saving conversation for session {session_id}")
    except Exception as e:
        logger.error(f"Error saving conversation: {str(e)}")