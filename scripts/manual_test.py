#!/usr/bin/env python3
"""
Manual testing script for interactive testing of the LangGraph WhatsApp Agent.
This allows you to send messages directly to your agent and see responses.
"""
import asyncio
import os
import sys
from pathlib import Path
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from langgraph_whatsapp.agent import Agent


class ManualTester:
    def __init__(self):
        self.agent = None
        self.conversation_id = "manual-test-session"
        
    async def initialize_agent(self):
        """Initialize the agent"""
        print("🤖 Initializing LangGraph WhatsApp Agent...")
        
        # Check environment
        required_env = {
            "LANGGRAPH_URL": os.getenv("LANGGRAPH_URL", "http://localhost:8123"),
            "LANGGRAPH_ASSISTANT_ID": os.getenv("LANGGRAPH_ASSISTANT_ID", "agent"),
            "CONFIG": os.getenv("CONFIG", "{}")
        }
        
        print("\n📋 Current Configuration:")
        for key, value in required_env.items():
            print(f"  {key}: {value}")
        
        # Set environment if needed
        for key, value in required_env.items():
            os.environ[key] = value
        
        try:
            self.agent = Agent()
            print("✅ Agent initialized successfully!")
            return True
        except Exception as e:
            print(f"❌ Failed to initialize agent: {str(e)}")
            print("\n💡 Troubleshooting:")
            print("  1. Make sure your LangGraph server is running: langgraph up")
            print("  2. Check your LANGGRAPH_URL is correct")
            print("  3. Verify your LANGGRAPH_ASSISTANT_ID exists")
            return False
    
    async def send_message(self, message: str, images: list = None) -> str:
        """Send a message to the agent"""
        try:
            print(f"\n📤 Sending: {message}")
            if images:
                print(f"🖼️  With {len(images)} image(s)")
            
            response = await self.agent.invoke(
                id=self.conversation_id,
                user_message=message,
                images=images
            )
            
            print(f"🤖 Response: {response}")
            return response
            
        except Exception as e:
            error_msg = f"❌ Error: {str(e)}"
            print(error_msg)
            return error_msg
    
    def create_test_image(self) -> dict:
        """Create a test image for testing"""
        # Simple 1x1 pixel PNG in base64
        test_image_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        return {
            "image_url": {
                "url": f"data:image/png;base64,{test_image_b64}"
            }
        }
    
    async def run_interactive_session(self):
        """Run an interactive testing session"""
        print("🎯 Manual Testing Session")
        print("=" * 50)
        print("Commands:")
        print("  /help     - Show this help")
        print("  /image    - Send a test image")
        print("  /config   - Show current config")
        print("  /quit     - Exit")
        print("  <message> - Send a message to the agent")
        print("=" * 50)
        
        while True:
            try:
                user_input = input("\n💬 You: ").strip()
                
                if not user_input:
                    continue
                
                if user_input == "/quit":
                    print("👋 Goodbye!")
                    break
                
                elif user_input == "/help":
                    print("\n📚 Available commands:")
                    print("  /help     - Show this help")
                    print("  /image    - Send a test image")
                    print("  /config   - Show current config")
                    print("  /quit     - Exit")
                    print("  <message> - Send a message to the agent")
                
                elif user_input == "/config":
                    print("\n⚙️  Current Configuration:")
                    print(f"  LANGGRAPH_URL: {os.getenv('LANGGRAPH_URL')}")
                    print(f"  ASSISTANT_ID: {os.getenv('LANGGRAPH_ASSISTANT_ID')}")
                    print(f"  CONFIG: {os.getenv('CONFIG')}")
                
                elif user_input == "/image":
                    test_image = self.create_test_image()
                    await self.send_message("What do you see in this image?", [test_image])
                
                elif user_input.startswith("/"):
                    print(f"❓ Unknown command: {user_input}")
                    print("Type /help for available commands")
                
                else:
                    await self.send_message(user_input)
                    
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Unexpected error: {str(e)}")
    
    async def run_predefined_tests(self):
        """Run a series of predefined tests"""
        print("🧪 Running Predefined Tests")
        print("=" * 50)
        
        test_cases = [
            {
                "name": "Basic Greeting",
                "message": "Hello! How are you today?",
                "images": None
            },
            {
                "name": "Calendar Request",
                "message": "Can you schedule a meeting for tomorrow at 2 PM?",
                "images": None
            },
            {
                "name": "Task Management",
                "message": "Add a task to my todo list: Review project documentation",
                "images": None
            },
            {
                "name": "Image Analysis",
                "message": "What do you see in this image?",
                "images": [self.create_test_image()]
            },
            {
                "name": "Complex Query",
                "message": "I need help organizing my week. I have three meetings and two deadlines coming up.",
                "images": None
            }
        ]
        
        results = []
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n🧪 Test {i}/{len(test_cases)}: {test_case['name']}")
            print("-" * 30)
            
            try:
                response = await self.send_message(
                    test_case["message"], 
                    test_case["images"]
                )
                
                # Simple success check - if we got a response, consider it successful
                success = len(response) > 0 and not response.startswith("❌")
                results.append((test_case["name"], success))
                
                print(f"✅ Status: {'PASSED' if success else 'FAILED'}")
                
            except Exception as e:
                print(f"❌ Failed: {str(e)}")
                results.append((test_case["name"], False))
        
        # Summary
        print("\n" + "=" * 50)
        print("📊 Test Results Summary:")
        passed = sum(1 for _, success in results if success)
        total = len(results)
        
        for name, success in results:
            status = "✅ PASSED" if success else "❌ FAILED"
            print(f"  {name}: {status}")
        
        print(f"\nOverall: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! Your agent is working great!")
        else:
            print("⚠️  Some tests failed. Check your agent configuration.")


async def main():
    """Main entry point"""
    tester = ManualTester()
    
    # Initialize agent
    if not await tester.initialize_agent():
        return False
    
    print("\n🎯 Choose testing mode:")
    print("1. Interactive session (chat with your agent)")
    print("2. Predefined tests (automated test suite)")
    
    try:
        choice = input("\nEnter your choice (1 or 2): ").strip()
        
        if choice == "1":
            await tester.run_interactive_session()
        elif choice == "2":
            await tester.run_predefined_tests()
        else:
            print("❌ Invalid choice. Please enter 1 or 2.")
            return False
            
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 