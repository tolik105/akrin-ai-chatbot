"""
Tests for NLP Engine
"""

import pytest
import asyncio
from src.core.nlp_engine import (
    NLPEngine, IntentRecognizer, EntityExtractor,
    Intent, Entity, NLUResult, DialogueState
)


@pytest.fixture
def nlp_engine():
    """Create NLP engine instance"""
    return NLPEngine()


@pytest.fixture
def intent_recognizer():
    """Create intent recognizer instance"""
    return IntentRecognizer()


@pytest.fixture
def entity_extractor():
    """Create entity extractor instance"""
    return EntityExtractor()


class TestIntentRecognizer:
    """Test intent recognition"""
    
    @pytest.mark.asyncio
    async def test_greeting_intent(self, intent_recognizer):
        """Test greeting intent recognition"""
        test_cases = [
            ("Hello there!", Intent.GREETING),
            ("Hi, how are you?", Intent.GREETING),
            ("Good morning", Intent.GREETING),
        ]
        
        for text, expected_intent in test_cases:
            intent, confidence = await intent_recognizer.process(text, {})
            assert intent == expected_intent
            assert confidence > 0
    
    @pytest.mark.asyncio
    async def test_password_reset_intent(self, intent_recognizer):
        """Test password reset intent recognition"""
        text = "I forgot my password and need to reset it"
        intent, confidence = await intent_recognizer.process(text, {})
        
        assert intent == Intent.PASSWORD_RESET
        assert confidence > 0
    
    @pytest.mark.asyncio
    async def test_unknown_intent(self, intent_recognizer):
        """Test unknown intent recognition"""
        text = "Random gibberish xyzabc123"
        intent, confidence = await intent_recognizer.process(text, {})
        
        assert intent == Intent.UNKNOWN
        assert confidence == 0.0


class TestEntityExtractor:
    """Test entity extraction"""
    
    @pytest.mark.asyncio
    async def test_email_extraction(self, entity_extractor):
        """Test email entity extraction"""
        text = "My email is john.doe@example.com"
        entities = await entity_extractor.process(text, {})
        
        assert len(entities) == 1
        assert entities[0].type == "email"
        assert entities[0].value == "john.doe@example.com"
        assert entities[0].confidence > 0.9
    
    @pytest.mark.asyncio
    async def test_ticket_number_extraction(self, entity_extractor):
        """Test ticket number extraction"""
        text = "I need help with ticket #12345"
        entities = await entity_extractor.process(text, {})
        
        assert len(entities) == 1
        assert entities[0].type == "ticket_number"
        assert entities[0].value == "12345"
    
    @pytest.mark.asyncio
    async def test_no_entities(self, entity_extractor):
        """Test when no entities are present"""
        text = "Hello, how are you?"
        entities = await entity_extractor.process(text, {})
        
        assert len(entities) == 0


class TestNLPEngine:
    """Test complete NLP engine"""
    
    @pytest.mark.asyncio
    async def test_process_message(self, nlp_engine):
        """Test message processing"""
        text = "I forgot my password for user@example.com"
        session_id = "test-session-123"
        
        result = await nlp_engine.process_message(text, session_id)
        
        assert isinstance(result, NLUResult)
        assert result.intent == Intent.PASSWORD_RESET
        assert len(result.entities) == 1
        assert result.entities[0].type == "email"
        assert result.original_text == text
    
    @pytest.mark.asyncio
    async def test_dialogue_state_management(self, nlp_engine):
        """Test dialogue state tracking"""
        session_id = "test-session-456"
        
        # First message
        await nlp_engine.process_message("Hello", session_id)
        state = nlp_engine.get_dialogue_state(session_id)
        
        assert state is not None
        assert state.session_id == session_id
        assert state.turn_count == 1
        assert state.current_intent == Intent.GREETING
        
        # Second message
        await nlp_engine.process_message("I need to reset my password", session_id)
        state = nlp_engine.get_dialogue_state(session_id)
        
        assert state.turn_count == 2
        assert state.current_intent == Intent.PASSWORD_RESET
    
    @pytest.mark.asyncio
    async def test_session_cleanup(self, nlp_engine):
        """Test session cleanup"""
        session_id = "test-session-789"
        
        await nlp_engine.process_message("Hello", session_id)
        assert nlp_engine.get_dialogue_state(session_id) is not None
        
        nlp_engine.clear_session(session_id)
        assert nlp_engine.get_dialogue_state(session_id) is None
    
    def test_human_handoff_detection(self, nlp_engine):
        """Test human handoff detection"""
        # Create a state that should trigger handoff
        state = DialogueState(
            session_id="test",
            user_id=None,
            current_intent=Intent.UNKNOWN,
            context={},
            turn_count=3,
            entities_collected={},
            awaiting_info=None
        )
        
        should_handoff = nlp_engine.dialogue_manager.should_handoff(state)
        assert should_handoff is True
        
        # Test explicit handoff request
        state.current_intent = Intent.HUMAN_HANDOFF
        state.turn_count = 1
        should_handoff = nlp_engine.dialogue_manager.should_handoff(state)
        assert should_handoff is True