"""
WebSocket implementation for real-time chat
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from typing import Dict, List, Optional, Set
import json
import asyncio
from datetime import datetime
import uuid

from src.core.nlp_engine import NLPEngine
from src.knowledge.rag_module import EnhancedRAG
from src.core.memory_cache import get_session_store
from src.utils.logging import chat_logger as logger

router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections for real-time chat"""
    
    def __init__(self):
        # Active connections by session_id
        self.active_connections: Dict[str, WebSocket] = {}
        # Agent connections
        self.agent_connections: Dict[str, WebSocket] = {}
        # Session to agent mapping
        self.session_agent_map: Dict[str, str] = {}
        # Waiting queue for customers
        self.waiting_queue: asyncio.Queue = asyncio.Queue()
        
    async def connect_customer(self, websocket: WebSocket, session_id: str):
        """Connect a customer"""
        await websocket.accept()
        self.active_connections[session_id] = websocket
        logger.info(f"Customer connected: {session_id}")
        
        # Send welcome message
        await self.send_personal_message({
            "type": "system",
            "message": "Welcome to AKRIN Support! How can I help you today?",
            "timestamp": datetime.utcnow().isoformat()
        }, websocket)
    
    async def connect_agent(self, websocket: WebSocket, agent_id: str):
        """Connect a support agent"""
        await websocket.accept()
        self.agent_connections[agent_id] = websocket
        logger.info(f"Agent connected: {agent_id}")
        
        # Notify agent of waiting customers
        waiting_count = self.waiting_queue.qsize()
        await self.send_personal_message({
            "type": "agent_status",
            "status": "connected",
            "waiting_customers": waiting_count,
            "timestamp": datetime.utcnow().isoformat()
        }, websocket)
    
    def disconnect(self, session_id: str):
        """Disconnect a customer"""
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            # Remove from agent mapping if exists
            if session_id in self.session_agent_map:
                del self.session_agent_map[session_id]
            logger.info(f"Customer disconnected: {session_id}")
    
    def disconnect_agent(self, agent_id: str):
        """Disconnect an agent"""
        if agent_id in self.agent_connections:
            del self.agent_connections[agent_id]
            # Find and reassign customers handled by this agent
            sessions_to_reassign = [
                session for session, assigned_agent 
                in self.session_agent_map.items() 
                if assigned_agent == agent_id
            ]
            for session in sessions_to_reassign:
                del self.session_agent_map[session]
                # Add back to waiting queue
                asyncio.create_task(self.waiting_queue.put(session))
            logger.info(f"Agent disconnected: {agent_id}")
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send message to specific websocket"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending message: {e}")
    
    async def broadcast_to_agents(self, message: dict):
        """Broadcast message to all connected agents"""
        disconnected = []
        for agent_id, websocket in self.agent_connections.items():
            try:
                await websocket.send_json(message)
            except:
                disconnected.append(agent_id)
        
        # Clean up disconnected agents
        for agent_id in disconnected:
            self.disconnect_agent(agent_id)
    
    async def route_customer_message(self, session_id: str, message: str) -> dict:
        """Route customer message to AI or human agent"""
        # Check if customer is connected to an agent
        if session_id in self.session_agent_map:
            agent_id = self.session_agent_map[session_id]
            if agent_id in self.agent_connections:
                # Forward to human agent
                await self.send_personal_message({
                    "type": "customer_message",
                    "session_id": session_id,
                    "message": message,
                    "timestamp": datetime.utcnow().isoformat()
                }, self.agent_connections[agent_id])
                
                return {
                    "type": "routed_to_agent",
                    "agent_id": agent_id
                }
        
        # No agent assigned, return for AI processing
        return {
            "type": "process_with_ai"
        }
    
    async def assign_agent_to_session(self, agent_id: str, session_id: str):
        """Assign an agent to handle a customer session"""
        self.session_agent_map[session_id] = agent_id
        
        # Notify customer
        if session_id in self.active_connections:
            await self.send_personal_message({
                "type": "agent_assigned",
                "message": "You've been connected to a human agent.",
                "agent_id": agent_id,
                "timestamp": datetime.utcnow().isoformat()
            }, self.active_connections[session_id])
        
        # Notify agent
        if agent_id in self.agent_connections:
            await self.send_personal_message({
                "type": "customer_assigned",
                "session_id": session_id,
                "message": "New customer assigned to you.",
                "timestamp": datetime.utcnow().isoformat()
            }, self.agent_connections[agent_id])
    
    async def request_human_handoff(self, session_id: str, reason: str = ""):
        """Add customer to queue for human handoff"""
        await self.waiting_queue.put({
            "session_id": session_id,
            "reason": reason,
            "requested_at": datetime.utcnow().isoformat()
        })
        
        # Notify all agents
        await self.broadcast_to_agents({
            "type": "new_customer_waiting",
            "waiting_count": self.waiting_queue.qsize(),
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Notify customer
        if session_id in self.active_connections:
            await self.send_personal_message({
                "type": "handoff_requested",
                "message": "I'm connecting you with a human agent. Please wait a moment.",
                "position_in_queue": self.waiting_queue.qsize(),
                "timestamp": datetime.utcnow().isoformat()
            }, self.active_connections[session_id])
    
    def get_active_sessions(self) -> List[str]:
        """Get list of active customer sessions"""
        return list(self.active_connections.keys())
    
    def get_available_agents(self) -> List[str]:
        """Get list of available agents"""
        # Agents not currently handling maximum customers
        return [
            agent_id for agent_id in self.agent_connections.keys()
            if sum(1 for a in self.session_agent_map.values() if a == agent_id) < 5  # Max 5 customers per agent
        ]


# Global connection manager
manager = ConnectionManager()

# Initialize AI components
nlp_engine = NLPEngine()
rag_module = EnhancedRAG()
session_store = get_session_store()


@router.websocket("/ws/chat/{session_id}")
async def websocket_chat_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for customer chat"""
    await manager.connect_customer(websocket, session_id)
    
    try:
        while True:
            # Receive message from customer
            data = await websocket.receive_json()
            message_text = data.get("message", "")
            
            if not message_text:
                continue
            
            logger.info(f"Received message from {session_id}: {message_text[:50]}...")
            
            # Route message (to agent or AI)
            routing_result = await manager.route_customer_message(session_id, message_text)
            
            if routing_result["type"] == "process_with_ai":
                # Process with AI
                try:
                    # Get or create session
                    session_data = await session_store.get(session_id) or {
                        "started_at": datetime.utcnow().isoformat(),
                        "messages": []
                    }
                    
                    # Process through NLP
                    nlu_result = await nlp_engine.process_message(
                        text=message_text,
                        session_id=session_id
                    )
                    
                    # Check if human handoff is needed
                    dialogue_state = nlp_engine.get_dialogue_state(session_id)
                    if nlp_engine.dialogue_manager.should_handoff(dialogue_state):
                        await manager.request_human_handoff(session_id, "AI escalation")
                        continue
                    
                    # Generate response using RAG
                    generation_result = await rag_module.process(
                        query=message_text,
                        context={
                            "session_id": session_id,
                            "intent": nlu_result.intent.value,
                            "turn_count": dialogue_state.turn_count
                        }
                    )
                    
                    # Send AI response
                    await websocket.send_json({
                        "type": "ai_response",
                        "message": generation_result.response,
                        "intent": nlu_result.intent.value,
                        "confidence": generation_result.confidence,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    
                    # Update session
                    session_data["messages"].extend([
                        {"role": "user", "content": message_text, "timestamp": datetime.utcnow().isoformat()},
                        {"role": "assistant", "content": generation_result.response, "timestamp": datetime.utcnow().isoformat()}
                    ])
                    await session_store.set(session_id, session_data)
                    
                except Exception as e:
                    logger.error(f"Error processing AI response: {e}")
                    await websocket.send_json({
                        "type": "error",
                        "message": "I encountered an error. Would you like to speak with a human agent?",
                        "timestamp": datetime.utcnow().isoformat()
                    })
            
            # Check for special commands
            if message_text.lower() in ["human", "agent", "help", "speak to human"]:
                await manager.request_human_handoff(session_id, "Customer request")
                
    except WebSocketDisconnect:
        manager.disconnect(session_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(session_id)


@router.websocket("/ws/agent/{agent_id}")
async def websocket_agent_endpoint(websocket: WebSocket, agent_id: str):
    """WebSocket endpoint for support agents"""
    # TODO: Add authentication for agents
    await manager.connect_agent(websocket, agent_id)
    
    try:
        while True:
            # Receive message from agent
            data = await websocket.receive_json()
            action = data.get("action")
            
            if action == "send_message":
                # Agent sending message to customer
                session_id = data.get("session_id")
                message = data.get("message")
                
                if session_id in manager.active_connections:
                    await manager.send_personal_message({
                        "type": "agent_message",
                        "message": message,
                        "agent_id": agent_id,
                        "timestamp": datetime.utcnow().isoformat()
                    }, manager.active_connections[session_id])
            
            elif action == "accept_customer":
                # Agent accepting a customer from queue
                if not manager.waiting_queue.empty():
                    customer_data = await manager.waiting_queue.get()
                    session_id = customer_data["session_id"]
                    await manager.assign_agent_to_session(agent_id, session_id)
            
            elif action == "transfer_customer":
                # Transfer customer to another agent
                session_id = data.get("session_id")
                new_agent_id = data.get("new_agent_id")
                
                if new_agent_id in manager.agent_connections:
                    await manager.assign_agent_to_session(new_agent_id, session_id)
            
            elif action == "end_chat":
                # End chat with customer
                session_id = data.get("session_id")
                
                if session_id in manager.active_connections:
                    await manager.send_personal_message({
                        "type": "chat_ended",
                        "message": "Chat ended by agent. Thank you for contacting AKRIN Support!",
                        "timestamp": datetime.utcnow().isoformat()
                    }, manager.active_connections[session_id])
                    
                    # Remove from mapping
                    if session_id in manager.session_agent_map:
                        del manager.session_agent_map[session_id]
            
            elif action == "get_queue_status":
                # Get current queue status
                await websocket.send_json({
                    "type": "queue_status",
                    "waiting_count": manager.waiting_queue.qsize(),
                    "active_chats": sum(1 for a in manager.session_agent_map.values() if a == agent_id),
                    "timestamp": datetime.utcnow().isoformat()
                })
                
    except WebSocketDisconnect:
        manager.disconnect_agent(agent_id)
    except Exception as e:
        logger.error(f"Agent WebSocket error: {e}")
        manager.disconnect_agent(agent_id)