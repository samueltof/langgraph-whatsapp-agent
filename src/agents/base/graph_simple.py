from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from langgraph_supervisor import create_supervisor
from agents.base.prompt import CALENDAR_AGENT_PROMPT, SUPERVISOR_PROMPT
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

async def build_agent():
    """
    Simple agent build without MCP dependencies for basic testing.
    """
    today = datetime.now().strftime("%Y-%m-%d")
    
    print("ℹ️ Building simple agent without MCP tools for basic testing...")
    
    # Create calendar agent without external tools
    calendar_agent = create_react_agent(
        model=ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",
        ),
        tools=[],  # No external tools - just basic LLM functionality
        name="calendar_agent",
        prompt=CALENDAR_AGENT_PROMPT.render(today=today)
    )
    
    # Create supervisor without external tools
    graph = create_supervisor(
        [calendar_agent],
        model=ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",
        ),
        output_mode="last_message",
        prompt=SUPERVISOR_PROMPT.render(),
        tools=[]  # No external tools
    )
    
    print("✅ Simple agent built successfully - ready for basic conversations!")
    return graph 