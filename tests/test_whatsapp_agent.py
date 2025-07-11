"""
Test the WhatsApp Agent class without Twilio integration.
This tests the Agent class that communicates with LangGraph.
"""
import asyncio
import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from langgraph_whatsapp.agent import Agent


async def test_agent_initialization():
    """Test that the Agent class initializes correctly"""
    print("🧪 Testing Agent Initialization...")
    
    # Mock environment variables if not set
    with patch.dict(os.environ, {
        'LANGGRAPH_URL': os.getenv('LANGGRAPH_URL', 'http://localhost:8123'),
        'LANGGRAPH_ASSISTANT_ID': os.getenv('LANGGRAPH_ASSISTANT_ID', 'agent'),
        'CONFIG': os.getenv('CONFIG', '{}')
    }):
        try:
            agent = Agent()
            print("✅ Agent initialized successfully")
            print(f"📡 LangGraph URL: {agent.client.api_url}")
            print(f"🆔 Assistant ID: {agent.graph_config}")
            return True
        except Exception as e:
            print(f"❌ Agent initialization failed: {str(e)}")
            return False


async def test_agent_invoke_text():
    """Test agent invoke with text message"""
    print("\n🧪 Testing Agent Text Message...")
    
    with patch.dict(os.environ, {
        'LANGGRAPH_URL': os.getenv('LANGGRAPH_URL', 'http://localhost:8123'),
        'LANGGRAPH_ASSISTANT_ID': os.getenv('LANGGRAPH_ASSISTANT_ID', 'agent'),
        'CONFIG': os.getenv('CONFIG', '{}')
    }):
        try:
            agent = Agent()
            
            # Test with a simple text message
            response = await agent.invoke(
                id="test-user-123",
                user_message="Hello! How are you today?"
            )
            
            print("✅ Agent invoke successful")
            print(f"🤖 Response type: {type(response)}")
            print(f"💬 Response: {response}")
            return True
            
        except Exception as e:
            print(f"❌ Agent invoke failed: {str(e)}")
            print(f"💡 Make sure LangGraph server is running at {os.getenv('LANGGRAPH_URL', 'http://localhost:8123')}")
            return False


async def test_agent_invoke_with_images():
    """Test agent invoke with images"""
    print("\n🧪 Testing Agent with Images...")
    
    with patch.dict(os.environ, {
        'LANGGRAPH_URL': os.getenv('LANGGRAPH_URL', 'http://localhost:8123'),
        'LANGGRAPH_ASSISTANT_ID': os.getenv('LANGGRAPH_ASSISTANT_ID', 'agent'),
        'CONFIG': os.getenv('CONFIG', '{}')
    }):
        try:
            agent = Agent()
            
            # Test with text + image
            test_images = [
                {
                    "image_url": {
                        "url": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
                    }
                }
            ]
            
            response = await agent.invoke(
                id="test-user-456",
                user_message="What do you see in this image?",
                images=test_images
            )
            
            print("✅ Agent invoke with images successful")
            print(f"🖼️ Response: {response}")
            return True
            
        except Exception as e:
            print(f"❌ Agent invoke with images failed: {str(e)}")
            return False


async def test_agent_error_handling():
    """Test agent error handling"""
    print("\n🧪 Testing Agent Error Handling...")
    
    with patch.dict(os.environ, {
        'LANGGRAPH_URL': 'http://invalid-url:9999',
        'LANGGRAPH_ASSISTANT_ID': 'test-agent',
        'CONFIG': '{}'
    }):
        try:
            agent = Agent()
            
            # This should fail due to invalid URL
            await agent.invoke(
                id="test-error",
                user_message="This should fail"
            )
            
            print("❌ Expected error but got success")
            return False
            
        except Exception as e:
            print(f"✅ Error handling works: {type(e).__name__}")
            return True


async def main():
    """Run all WhatsApp agent tests"""
    print("🚀 Starting WhatsApp Agent Tests")
    print("=" * 50)
    
    # Check environment
    langgraph_url = os.getenv('LANGGRAPH_URL')
    if not langgraph_url:
        print("⚠️  LANGGRAPH_URL not set, using default: http://localhost:8123")
        print("💡 Make sure your LangGraph server is running")
    
    # Run tests
    test1_passed = await test_agent_initialization()
    test2_passed = await test_agent_invoke_text()
    test3_passed = await test_agent_invoke_with_images()
    test4_passed = await test_agent_error_handling()
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"✅ Initialization: {'PASSED' if test1_passed else 'FAILED'}")
    print(f"✅ Text Message: {'PASSED' if test2_passed else 'FAILED'}")
    print(f"✅ Image Message: {'PASSED' if test3_passed else 'FAILED'}")
    print(f"✅ Error Handling: {'PASSED' if test4_passed else 'FAILED'}")
    
    all_passed = all([test1_passed, test2_passed, test3_passed, test4_passed])
    
    if all_passed:
        print("🎉 All WhatsApp agent tests passed!")
    else:
        print("❌ Some tests failed. Check your configuration.")
    
    return all_passed


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 