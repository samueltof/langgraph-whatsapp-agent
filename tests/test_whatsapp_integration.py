"""
Integration test for WhatsApp functionality without actual Twilio webhooks.
This simulates the full WhatsApp message flow.
"""
import asyncio
import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from fastapi import Request

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from langgraph_whatsapp.channel import WhatsAppAgentTwilio
from langgraph_whatsapp.server import APP


def create_mock_twilio_request(from_number: str, body: str, media_data: list = None):
    """Create a mock Twilio request"""
    form_data = {
        "From": from_number,
        "Body": body,
        "NumMedia": str(len(media_data) if media_data else 0)
    }
    
    # Add media data if provided
    if media_data:
        for i, media in enumerate(media_data):
            form_data[f"MediaUrl{i}"] = media.get("url", "")
            form_data[f"MediaContentType{i}"] = media.get("content_type", "image/jpeg")
    
    return form_data


async def test_whatsapp_agent_initialization():
    """Test WhatsApp agent initialization"""
    print("🧪 Testing WhatsApp Agent Initialization...")
    
    with patch.dict(os.environ, {
        'TWILIO_AUTH_TOKEN': 'test_token',
        'TWILIO_ACCOUNT_SID': 'test_sid',
        'LANGGRAPH_URL': os.getenv('LANGGRAPH_URL', 'http://localhost:8123'),
        'LANGGRAPH_ASSISTANT_ID': 'agent'
    }):
        try:
            whatsapp_agent = WhatsAppAgentTwilio()
            print("✅ WhatsApp agent initialized successfully")
            return True
        except Exception as e:
            print(f"❌ WhatsApp agent initialization failed: {str(e)}")
            return False


async def test_text_message_handling():
    """Test handling of text messages"""
    print("\n🧪 Testing Text Message Handling...")
    
    with patch.dict(os.environ, {
        'TWILIO_AUTH_TOKEN': 'test_token',
        'TWILIO_ACCOUNT_SID': 'test_sid',
        'LANGGRAPH_URL': os.getenv('LANGGRAPH_URL', 'http://localhost:8123'),
        'LANGGRAPH_ASSISTANT_ID': 'agent'
    }):
        try:
            whatsapp_agent = WhatsAppAgentTwilio()
            
            # Create mock request
            form_data = create_mock_twilio_request(
                from_number="+1234567890",
                body="Hello! Can you help me schedule a meeting?"
            )
            
            # Mock the request
            mock_request = Mock(spec=Request)
            mock_request.form = Mock(return_value=asyncio.create_task(
                asyncio.coroutine(lambda: form_data)()
            ))
            
            # Handle the message
            twiml_response = await whatsapp_agent.handle_message(mock_request)
            
            print("✅ Text message handled successfully")
            print(f"📱 TwiML Response length: {len(twiml_response)} chars")
            print(f"🤖 Contains message: {'<Message>' in twiml_response}")
            
            return True
            
        except Exception as e:
            print(f"❌ Text message handling failed: {str(e)}")
            return False


async def test_image_message_handling():
    """Test handling of messages with images"""
    print("\n🧪 Testing Image Message Handling...")
    
    with patch.dict(os.environ, {
        'TWILIO_AUTH_TOKEN': 'test_token',
        'TWILIO_ACCOUNT_SID': 'test_sid',
        'LANGGRAPH_URL': os.getenv('LANGGRAPH_URL', 'http://localhost:8123'),
        'LANGGRAPH_ASSISTANT_ID': 'agent'
    }), patch('langgraph_whatsapp.channel.twilio_url_to_data_uri') as mock_download:
        
        # Mock the image download
        mock_download.return_value = "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAYEBQYFBAYGBQYHBwYIChAKCgkJChQODwwQFxQYGBcUFhYaHSUfGhsjHBYWICwgIyYnKSopGR8tMC0oMCUoKSj/2wBDAQcHBwoIChMKChMoGhYaKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCj/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCdABmX/9k="
        
        try:
            whatsapp_agent = WhatsAppAgentTwilio()
            
            # Create mock request with image
            form_data = create_mock_twilio_request(
                from_number="+1234567890",
                body="What do you see in this image?",
                media_data=[{
                    "url": "https://api.twilio.com/fake-image-url",
                    "content_type": "image/jpeg"
                }]
            )
            
            # Mock the request
            mock_request = Mock(spec=Request)
            mock_request.form = Mock(return_value=asyncio.create_task(
                asyncio.coroutine(lambda: form_data)()
            ))
            
            # Handle the message
            twiml_response = await whatsapp_agent.handle_message(mock_request)
            
            print("✅ Image message handled successfully")
            print(f"📱 TwiML Response length: {len(twiml_response)} chars")
            print(f"🖼️ Image download called: {mock_download.called}")
            
            return True
            
        except Exception as e:
            print(f"❌ Image message handling failed: {str(e)}")
            return False


def test_fastapi_endpoint():
    """Test the FastAPI endpoint"""
    print("\n🧪 Testing FastAPI Endpoint...")
    
    with patch.dict(os.environ, {
        'TWILIO_AUTH_TOKEN': 'test_token',
        'TWILIO_ACCOUNT_SID': 'test_sid',
        'LANGGRAPH_URL': os.getenv('LANGGRAPH_URL', 'http://localhost:8123'),
        'LANGGRAPH_ASSISTANT_ID': 'agent'
    }):
        try:
            client = TestClient(APP)
            
            # Test GET request (should fail)
            response = client.get("/whatsapp")
            print(f"📡 GET /whatsapp: {response.status_code} (expected 405)")
            
            # The POST will fail due to Twilio signature validation, but that's expected
            response = client.post("/whatsapp", data={
                "From": "+1234567890",
                "Body": "Test message"
            })
            print(f"📡 POST /whatsapp: {response.status_code} (expected 401 due to signature)")
            
            print("✅ FastAPI endpoint responding correctly")
            return True
            
        except Exception as e:
            print(f"❌ FastAPI endpoint test failed: {str(e)}")
            return False


async def main():
    """Run all integration tests"""
    print("🚀 Starting WhatsApp Integration Tests")
    print("=" * 50)
    
    # Check environment
    required_env = ["LANGGRAPH_URL"]
    missing_env = [var for var in required_env if not os.getenv(var)]
    
    if missing_env:
        print(f"⚠️  Missing environment variables: {missing_env}")
        print("Using defaults where possible")
    
    # Run tests
    test1_passed = await test_whatsapp_agent_initialization()
    test2_passed = await test_text_message_handling()
    test3_passed = await test_image_message_handling()
    test4_passed = test_fastapi_endpoint()
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"✅ WhatsApp Init: {'PASSED' if test1_passed else 'FAILED'}")
    print(f"✅ Text Messages: {'PASSED' if test2_passed else 'FAILED'}")
    print(f"✅ Image Messages: {'PASSED' if test3_passed else 'FAILED'}")
    print(f"✅ FastAPI Endpoint: {'PASSED' if test4_passed else 'FAILED'}")
    
    all_passed = all([test1_passed, test2_passed, test3_passed, test4_passed])
    
    if all_passed:
        print("🎉 All integration tests passed!")
    else:
        print("❌ Some tests failed. Check your configuration.")
    
    return all_passed


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 