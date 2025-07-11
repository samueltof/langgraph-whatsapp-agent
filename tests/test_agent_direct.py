"""
Direct testing of the LangGraph agent without WhatsApp integration.
This tests the core agent functionality in isolation.
"""
import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agents.base.graph import build_agent


async def test_agent_direct():
    """Test the LangGraph agent directly"""
    print("🧪 Testing LangGraph Agent Direct...")
    
    # Test simple message
    async with build_agent() as agent:
        print("✅ Agent initialized successfully")
        
        # Test message input
        test_input = {
            "messages": [
                {
                    "role": "user", 
                    "content": "Hello! Can you help me schedule a meeting for tomorrow at 2 PM?"
                }
            ]
        }
        
        print(f"📤 Sending test message: {test_input['messages'][0]['content']}")
        
        try:
            # Invoke the agent
            response = await agent.ainvoke(
                test_input,
                config={"thread_id": "test-thread-123"}
            )
            
            print("✅ Agent responded successfully!")
            print(f"🤖 Response: {response['messages'][-1].content}")
            
        except Exception as e:
            print(f"❌ Agent failed: {str(e)}")
            return False
    
    return True


async def test_agent_with_calendar_task():
    """Test agent with a calendar-specific task"""
    print("\n🧪 Testing Calendar Agent...")
    
    async with build_agent() as agent:
        test_input = {
            "messages": [
                {
                    "role": "user", 
                    "content": "Schedule a team standup meeting for tomorrow at 9 AM"
                }
            ]
        }
        
        print(f"📤 Calendar task: {test_input['messages'][0]['content']}")
        
        try:
            response = await agent.ainvoke(
                test_input,
                config={"thread_id": "calendar-test-456"}
            )
            
            print("✅ Calendar agent responded!")
            print(f"🗓️ Response: {response['messages'][-1].content}")
            
        except Exception as e:
            print(f"❌ Calendar agent failed: {str(e)}")
            return False
    
    return True


async def main():
    """Run all direct agent tests"""
    print("🚀 Starting Direct Agent Tests")
    print("=" * 50)
    
    # Check environment variables
    required_env = ["ZAPIER_URL_MCP", "SUPERMEMORY_URL_MCP"]
    missing_env = [var for var in required_env if not os.getenv(var)]
    
    if missing_env:
        print(f"⚠️  Warning: Missing environment variables: {missing_env}")
        print("Some agent features may not work properly")
    
    # Run tests
    test1_passed = await test_agent_direct()
    test2_passed = await test_agent_with_calendar_task()
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"✅ Basic Agent Test: {'PASSED' if test1_passed else 'FAILED'}")
    print(f"✅ Calendar Agent Test: {'PASSED' if test2_passed else 'FAILED'}")
    
    if test1_passed and test2_passed:
        print("🎉 All direct agent tests passed!")
        return True
    else:
        print("❌ Some tests failed. Check your agent configuration.")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 