"""
Core NLP Engine for AKRIN AI Chatbot
Implements intent recognition, entity extraction, and dialogue management
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import asyncio
from abc import ABC, abstractmethod


class Intent(Enum):
    """Supported chatbot intents"""
    GREETING = "greeting"
    FAREWELL = "farewell"
    TECH_SUPPORT = "tech_support"
    PASSWORD_RESET = "password_reset"
    SERVICE_STATUS = "service_status"
    CREATE_TICKET = "create_ticket"
    BILLING_INQUIRY = "billing_inquiry"
    GENERAL_INQUIRY = "general_inquiry"
    HUMAN_HANDOFF = "human_handoff"
    UNKNOWN = "unknown"


@dataclass
class Entity:
    """Extracted entity from user input"""
    type: str
    value: str
    confidence: float
    start_pos: int
    end_pos: int


@dataclass
class NLUResult:
    """Result of NLU processing"""
    intent: Intent
    intent_confidence: float
    entities: List[Entity]
    original_text: str
    processed_text: str


@dataclass
class DialogueState:
    """Current state of the conversation"""
    session_id: str
    user_id: Optional[str]
    current_intent: Optional[Intent]
    context: Dict[str, any]
    turn_count: int
    entities_collected: Dict[str, str]
    awaiting_info: Optional[str]
    handoff_requested: bool = False


class NLPProcessor(ABC):
    """Abstract base class for NLP processors"""
    
    @abstractmethod
    async def process(self, text: str, context: Dict) -> Dict:
        """Process text and return results"""
        pass


class IntentRecognizer(NLPProcessor):
    """Recognizes user intent from text"""
    
    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path
        # In production, load actual ML model here
        
    async def process(self, text: str, context: Dict) -> Tuple[Intent, float]:
        """
        Recognize intent from user text
        Returns: (Intent, confidence_score)
        """
        # Placeholder implementation - replace with actual ML model
        text_lower = text.lower()
        
        # Simple rule-based intent detection for MVP
        intent_patterns = {
            Intent.GREETING: ["hello", "hi", "hey", "good morning"],
            Intent.FAREWELL: ["bye", "goodbye", "see you", "thanks"],
            Intent.PASSWORD_RESET: ["password", "reset", "forgot", "can't login"],
            Intent.SERVICE_STATUS: ["status", "down", "working", "issue"],
            Intent.CREATE_TICKET: ["ticket", "problem", "help", "support"],
            Intent.BILLING_INQUIRY: ["bill", "invoice", "payment", "charge"],
            Intent.HUMAN_HANDOFF: ["human", "agent", "person", "talk to someone"]
        }
        
        scores = {}
        for intent, patterns in intent_patterns.items():
            score = sum(1 for pattern in patterns if pattern in text_lower)
            if score > 0:
                scores[intent] = score / len(patterns)
        
        if scores:
            best_intent = max(scores, key=scores.get)
            return best_intent, scores[best_intent]
        
        return Intent.UNKNOWN, 0.0


class EntityExtractor(NLPProcessor):
    """Extracts entities from user text"""
    
    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path
        
    async def process(self, text: str, context: Dict) -> List[Entity]:
        """
        Extract entities from text
        Returns: List of Entity objects
        """
        entities = []
        
        # Placeholder implementation - replace with actual NER model
        # Extract email patterns
        import re
        
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        for match in re.finditer(email_pattern, text):
            entities.append(Entity(
                type="email",
                value=match.group(),
                confidence=0.95,
                start_pos=match.start(),
                end_pos=match.end()
            ))
        
        # Extract ticket numbers
        ticket_pattern = r'\b(?:ticket|case)\s*#?\s*(\d+)\b'
        for match in re.finditer(ticket_pattern, text, re.IGNORECASE):
            entities.append(Entity(
                type="ticket_number",
                value=match.group(1),
                confidence=0.9,
                start_pos=match.start(),
                end_pos=match.end()
            ))
        
        return entities


class DialogueManager:
    """Manages conversation flow and state"""
    
    def __init__(self):
        self.sessions: Dict[str, DialogueState] = {}
        
    def get_or_create_session(self, session_id: str, user_id: Optional[str] = None) -> DialogueState:
        """Get existing session or create new one"""
        if session_id not in self.sessions:
            self.sessions[session_id] = DialogueState(
                session_id=session_id,
                user_id=user_id,
                current_intent=None,
                context={},
                turn_count=0,
                entities_collected={},
                awaiting_info=None
            )
        return self.sessions[session_id]
    
    def update_state(self, session_id: str, intent: Intent, entities: List[Entity]) -> DialogueState:
        """Update dialogue state with new information"""
        state = self.get_or_create_session(session_id)
        state.current_intent = intent
        state.turn_count += 1
        
        # Update collected entities
        for entity in entities:
            state.entities_collected[entity.type] = entity.value
        
        # Check if we need more information
        state.awaiting_info = self._check_missing_info(state)
        
        return state
    
    def _check_missing_info(self, state: DialogueState) -> Optional[str]:
        """Check what information is missing for current intent"""
        required_info = {
            Intent.PASSWORD_RESET: ["email"],
            Intent.CREATE_TICKET: ["issue_description"],
            Intent.SERVICE_STATUS: ["service_name"],
        }
        
        if state.current_intent in required_info:
            for info in required_info[state.current_intent]:
                if info not in state.entities_collected:
                    return info
        
        return None
    
    def should_handoff(self, state: DialogueState) -> bool:
        """Determine if conversation should be handed off to human"""
        # Handoff if explicitly requested
        if state.handoff_requested or state.current_intent == Intent.HUMAN_HANDOFF:
            return True
        
        # Handoff if conversation is too long
        if state.turn_count > 10:
            return True
        
        # Handoff if stuck on unknown intent
        if state.current_intent == Intent.UNKNOWN and state.turn_count > 2:
            return True
        
        return False


class NLPEngine:
    """Main NLP engine coordinating all components"""
    
    def __init__(self):
        self.intent_recognizer = IntentRecognizer()
        self.entity_extractor = EntityExtractor()
        self.dialogue_manager = DialogueManager()
    
    async def process_message(self, 
                            text: str, 
                            session_id: str,
                            user_id: Optional[str] = None,
                            context: Optional[Dict] = None) -> NLUResult:
        """
        Process incoming message and return NLU result
        """
        context = context or {}
        
        # Get current dialogue state
        state = self.dialogue_manager.get_or_create_session(session_id, user_id)
        
        # Process in parallel for efficiency
        intent_task = self.intent_recognizer.process(text, context)
        entity_task = self.entity_extractor.process(text, context)
        
        (intent, confidence), entities = await asyncio.gather(intent_task, entity_task)
        
        # Update dialogue state
        self.dialogue_manager.update_state(session_id, intent, entities)
        
        # Create and return result
        return NLUResult(
            intent=intent,
            intent_confidence=confidence,
            entities=entities,
            original_text=text,
            processed_text=text.lower().strip()
        )
    
    def get_dialogue_state(self, session_id: str) -> Optional[DialogueState]:
        """Get current dialogue state for session"""
        return self.dialogue_manager.sessions.get(session_id)
    
    def clear_session(self, session_id: str):
        """Clear session data"""
        if session_id in self.dialogue_manager.sessions:
            del self.dialogue_manager.sessions[session_id]