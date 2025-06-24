#!/usr/bin/env python3
"""
Test API keys to ensure they're working
"""

import os
import sys
import asyncio
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()


async def test_openai():
    """Test OpenAI API key"""
    try:
        import openai
        
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Test with a simple completion
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Say 'API key works!'"}],
            max_tokens=10
        )
        
        print("✅ OpenAI API Key: Working")
        print(f"   Response: {response.choices[0].message.content}")
        return True
        
    except Exception as e:
        print(f"❌ OpenAI API Key: Failed - {str(e)}")
        return False


async def test_anthropic():
    """Test Anthropic API key"""
    try:
        import anthropic
        
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        
        # Test with a simple completion
        response = client.messages.create(
            model="claude-3-sonnet-20240229",
            messages=[{"role": "user", "content": "Say 'API key works!'"}],
            max_tokens=10
        )
        
        print("✅ Anthropic API Key: Working")
        print(f"   Response: {response.content[0].text}")
        return True
        
    except Exception as e:
        print(f"❌ Anthropic API Key: Failed - {str(e)}")
        return False


async def test_google_ai():
    """Test Google AI API key"""
    if not os.getenv("GOOGLE_AI_API_KEY"):
        print("⚠️  Google AI API Key: Not configured")
        return None
        
    try:
        import google.generativeai as genai
        
        genai.configure(api_key=os.getenv("GOOGLE_AI_API_KEY"))
        
        # Test with a simple completion
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content("Say 'API key works!'")
        
        print("✅ Google AI API Key: Working")
        print(f"   Response: {response.text}")
        return True
        
    except Exception as e:
        print(f"❌ Google AI API Key: Failed - {str(e)}")
        return False


async def test_pinecone():
    """Test Pinecone API key"""
    if not os.getenv("PINECONE_API_KEY"):
        print("⚠️  Pinecone API Key: Not configured")
        return None
        
    try:
        from src.knowledge.pinecone_vector_store import get_pinecone_store
        
        vector_store = get_pinecone_store()
        
        # Get stats to verify connection
        stats = vector_store.get_stats()
        
        if 'total_vectors' in stats:
            print("✅ Pinecone API Key: Working")
            print(f"   Index: {stats.get('index_name', 'N/A')}")
            print(f"   Total vectors: {stats.get('total_vectors', 0)}")
            return True
        else:
            print("❌ Pinecone API Key: Failed to get stats")
            return False
            
    except Exception as e:
        print(f"❌ Pinecone API Key: Failed - {str(e)}")
        return False


async def test_local_vector_store():
    """Test local vector store (ChromaDB)"""
    try:
        from src.knowledge.local_vector_store import get_vector_store
        
        vector_store = get_vector_store()
        
        # Test adding a document
        test_doc = {
            'id': 'test-doc-1',
            'content': 'This is a test document for the AKRIN chatbot.',
            'metadata': {'category': 'test'}
        }
        
        vector_store.add_documents([test_doc])
        
        # Test searching
        results = vector_store.search("test document", top_k=1)
        
        if results and results[0]['id'] == 'test-doc-1':
            print("✅ Local Vector Store (ChromaDB): Working")
            print(f"   Found {len(results)} result(s)")
            
            # Clean up
            vector_store.delete_document('test-doc-1')
            return True
        else:
            print("❌ Local Vector Store: Search failed")
            return False
            
    except Exception as e:
        print(f"❌ Local Vector Store: Failed - {str(e)}")
        return False


async def main():
    """Run all tests"""
    print("🔍 Testing API Keys and Services...")
    print("=" * 50)
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("❌ Error: .env file not found!")
        print("   Please copy .env.example to .env and add your API keys")
        return
    
    # Run tests
    results = await asyncio.gather(
        test_openai(),
        test_anthropic(),
        test_google_ai(),
        test_pinecone(),
        test_local_vector_store(),
        return_exceptions=True
    )
    
    print("\n" + "=" * 50)
    print("📊 Summary:")
    
    # Count successes
    successes = sum(1 for r in results if r is True)
    failures = sum(1 for r in results if r is False)
    skipped = sum(1 for r in results if r is None)
    
    print(f"   ✅ Successful: {successes}")
    print(f"   ❌ Failed: {failures}")
    print(f"   ⚠️  Skipped: {skipped}")
    
    if failures > 0:
        print("\n⚠️  Some API keys are not working properly.")
        print("   Please check your .env file and ensure the keys are correct.")
    else:
        print("\n🎉 All configured API keys are working!")


if __name__ == "__main__":
    asyncio.run(main())