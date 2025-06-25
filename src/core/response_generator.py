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
    
    # Enhanced intent-based response mapping
    responses = {
        "greeting": "Hello! I'm AKRIN's AI assistant. How can I help you with your IT needs today? I can assist with:\n• IT Support & Troubleshooting\n• Cloud Solutions\n• Cybersecurity Services\n• Digital Transformation\n• Managed IT Services",

        "general_inquiry": "AKRIN株式会社 offers comprehensive IT solutions including:\n\n🔧 **Managed IT Support** - 24/7 monitoring and maintenance\n☁️ **Cloud Solutions** - Migration, management, and optimization\n🔒 **Cybersecurity** - Advanced threat protection and compliance\n🚀 **Digital Transformation** - Modernizing your business processes\n📊 **IT Consulting** - Strategic technology planning\n\nWhat specific area interests you most?",

        "tech_support": "I'm here to help with your technical issue! For immediate support:\n\n🔧 **24/7 Support Hotline**: +81-3-6821-1223\n📧 **Email Support**: support@akrin.jp\n💬 **Live Chat**: Available now\n\nCan you describe the specific problem you're experiencing? I'll do my best to help or connect you with the right specialist.",

        "billing_inquiry": "For pricing and billing inquiries:\n\n💰 **Custom Quotes**: Tailored to your specific needs\n📋 **Service Packages**: Flexible monthly plans available\n📞 **Sales Team**: +81-3-6821-1223\n📧 **Billing Support**: billing@akrin.jp\n\nWould you like me to connect you with our sales team for a personalized consultation?",

        "password_reset": "I can help you with password reset! Here's what you can do:\n\n1️⃣ **Self-Service Portal**: Visit our client portal\n2️⃣ **Call Support**: +81-3-6821-1223 (24/7)\n3️⃣ **Email**: support@akrin.jp with your username\n\nFor security, our technicians will verify your identity before resetting. Do you need immediate assistance?",

        "service_status": "To check service status:\n\n🟢 **Status Page**: https://status.akrin.jp\n📱 **Real-time Monitoring**: Available in client portal\n📞 **Direct Line**: +81-3-6821-1223\n\nIs there a specific service you're concerned about? I can help check its current status.",

        "create_ticket": "I'll help you create a support ticket:\n\n🎫 **Online Portal**: Fastest way to submit\n📞 **Phone**: +81-3-6821-1223 (immediate assistance)\n📧 **Email**: support@akrin.jp\n\nWhat type of issue are you experiencing? This helps us route to the right specialist.",

        "human_handoff": "I'll connect you with a human specialist right away!\n\n👨‍💻 **Technical Support**: +81-3-6821-1223\n💼 **Sales Team**: sales@akrin.jp\n📧 **General Inquiries**: info@akrin.jp\n\nOur team is available 24/7 for technical issues. What type of specialist would be most helpful?",

        "farewell": "Thank you for choosing AKRIN! 🙏\n\nRemember:\n📞 24/7 Support: +81-3-6821-1223\n📧 Email: support@akrin.jp\n🌐 Portal: https://portal.akrin.jp\n\nHave a great day, and don't hesitate to reach out anytime!",

        "unknown": "I want to make sure I understand your needs correctly. AKRIN specializes in:\n\n• **IT Support & Troubleshooting**\n• **Cloud Infrastructure**\n• **Cybersecurity Solutions**\n• **Digital Transformation**\n• **Managed Services**\n\nCould you tell me more about what you're looking for? Or would you prefer to speak directly with our team at +81-3-6821-1223?"
    }
    
    # Get response based on intent
    response = responses.get(intent, responses["unknown"])
    
    # Add entity-specific information and context
    if entities:
        if "service_type" in entities:
            service_type = entities["service_type"]
            response += f"\n\n🎯 **{service_type}**: I can provide detailed information about this service. Would you like to know about features, pricing, or implementation?"

        if "urgency" in entities and entities["urgency"] == "urgent":
            response += "\n\n🚨 **URGENT**: For immediate assistance, please call our 24/7 emergency line at +81-3-6821-1223."

        if "email" in entities:
            response += "\n\n📧 I see you provided an email address. Our team will follow up with you shortly."

    # Add contextual suggestions based on message content
    message_lower = message.lower()
    if any(word in message_lower for word in ["cloud", "aws", "azure", "migration"]):
        response += "\n\n☁️ **Cloud Services**: We're certified partners with AWS, Azure, and Google Cloud. Would you like to discuss migration strategies?"

    if any(word in message_lower for word in ["security", "cyber", "breach", "protection"]):
        response += "\n\n🔒 **Cybersecurity**: Our security team can perform assessments and implement protection measures. Interested in a security audit?"

    if any(word in message_lower for word in ["backup", "disaster", "recovery"]):
        response += "\n\n💾 **Backup & Recovery**: We offer comprehensive disaster recovery solutions. Would you like to discuss your backup strategy?"
    
    # Add helpful suggestions based on intent
    suggestions_map = {
        "greeting": [
            "What IT services do you offer?",
            "I need technical support",
            "Tell me about cloud solutions",
            "Request a consultation"
        ],
        "general_inquiry": [
            "Cloud migration services",
            "Cybersecurity solutions",
            "Managed IT support",
            "Get a custom quote"
        ],
        "tech_support": [
            "Password reset help",
            "System not working",
            "Network connectivity issues",
            "Software problems"
        ],
        "unknown": [
            "What services do you provide?",
            "I need IT support",
            "Pricing information",
            "Speak to a specialist"
        ]
    }

    suggestions = suggestions_map.get(intent, [
        "Tell me about your services",
        "I need help with IT",
        "Request consultation",
        "Contact support team"
    ])
    
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
