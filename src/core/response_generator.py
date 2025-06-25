"""
Fallback response generator for when RAG module is not available
"""

from typing import Dict, Any
from dataclasses import dataclass
import asyncio
from src.utils.logging import chat_logger as logger


@dataclass
class FallbackGenerationResult:
    """Result from fallback response generation"""
    response: str
    confidence: float
    sources: list
    validation_passed: bool
    metadata: Dict[str, Any]


async def generate_fallback_response(
    message: str,
    intent: str,
    entities: Dict[str, str],
    session_id: str
) -> FallbackGenerationResult:
    """
    Generate a fallback response when RAG module is not available
    
    Args:
        message: User's message
        intent: Detected intent
        entities: Extracted entities
        session_id: Session identifier
        
    Returns:
        FallbackGenerationResult with appropriate response
    """
    
    logger.info(f"Generating fallback response for intent: {intent}")
    
    # Intent-based response mapping
    responses = {
        "greeting": "Hello! I'm AKRIN's AI assistant. How can I help you with your IT needs today?",
        "service_inquiry": "AKRIN offers comprehensive IT services including managed IT support, cloud solutions, cybersecurity, and digital transformation. What specific service are you interested in?",
        "pricing_inquiry": "Our pricing varies based on your specific needs. I'd be happy to connect you with our sales team for a customized quote. Would you like me to schedule a consultation?",
        "support_request": "I understand you need technical support. For immediate assistance, please call our support line at +81-3-6821-1223 or email support@akrin.jp. How can I help you right now?",
        "company_info": "AKRIN株式会社 is a leading IT solutions provider in Japan, specializing in managed IT services, cloud infrastructure, and digital transformation for businesses of all sizes.",
        "contact_info": "You can reach AKRIN at:\n📞 Phone: +81-3-6821-1223\n📧 Email: info@akrin.jp\n🌐 Website: https://akrin.jp\n📍 Office: Tokyo, Japan",
        "goodbye": "Thank you for contacting AKRIN! If you need further assistance, don't hesitate to reach out. Have a great day!",
        "unknown": "I'm here to help with your IT needs. Could you please provide more details about what you're looking for? You can also contact our team directly at +81-3-6821-1223."
    }
    
    # Get response based on intent
    response = responses.get(intent, responses["unknown"])
    
    # Add entity-specific information if available
    if entities:
        if "service_type" in entities:
            service_type = entities["service_type"]
            response += f"\n\nI see you're interested in {service_type}. Let me know if you'd like more specific information about this service."
        
        if "urgency" in entities and entities["urgency"] == "urgent":
            response += "\n\n⚠️ For urgent issues, please call our 24/7 support line at +81-3-6821-1223."
    
    # Add helpful suggestions
    suggestions = [
        "Tell me about your IT services",
        "I need technical support",
        "Request a consultation",
        "Contact information"
    ]
    
    return FallbackGenerationResult(
        response=response,
        confidence=0.8,  # Moderate confidence for fallback responses
        sources=["AKRIN Knowledge Base"],
        validation_passed=True,
        metadata={
            "fallback_used": True,
            "intent": intent,
            "entities": entities,
            "suggestions": suggestions
        }
    )
