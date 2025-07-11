from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from langgraph_supervisor import create_supervisor
from langchain_mcp_adapters.client import MultiServerMCPClient
from agents.base.prompt import CALENDAR_AGENT_PROMPT, SUPERVISOR_PROMPT
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

async def build_agent():
    """
    Build the agent graph using the official MCP adapter pattern for LangGraph API Server.
    Following: https://github.com/langchain-ai/langchain-mcp-adapters
    """
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Configure all MCP servers in a single dictionary (official pattern)
    mcp_servers = {}
    
    # Add Zapier server if URL is provided
    zapier_url = os.getenv("ZAPIER_URL_MCP")
    if zapier_url:
        mcp_servers["zapier"] = {
            "url": zapier_url,
            "transport": "sse"
        }
    
    # Add Supermemory server if URL is provided  
    supermemory_url = os.getenv("SUPERMEMORY_URL_MCP")
    if supermemory_url:
        mcp_servers["supermemory"] = {
            "url": supermemory_url,
            "transport": "sse"
        }
    
    # Get tools from MCP servers using the official pattern
    tools = []
    if mcp_servers:
        try:
            # Single client for all servers (official recommended approach)
            client = MultiServerMCPClient(mcp_servers)
            tools = await client.get_tools()
            print(f"✅ Loaded {len(tools)} MCP tools from {list(mcp_servers.keys())}")
        except Exception as e:
            print(f"⚠️ Warning: Could not load MCP tools: {e}")
            print("Continuing without MCP tools...")
    else:
        print("ℹ️ No MCP server URLs configured, running without external tools")
    
    # Create calendar agent with available tools
    calendar_agent = create_react_agent(
        model=ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",
        ),
        tools=tools,  # All tools available to calendar agent
        name="calendar_agent",
        prompt=CALENDAR_AGENT_PROMPT.render(today=today)
    )
    
    # Create supervisor with same tools
    graph = create_supervisor(
        [calendar_agent],
        model=ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",
        ),
        output_mode="last_message",
        prompt=SUPERVISOR_PROMPT.render(),
        tools=tools  # Supervisor has access to all tools too
    )
    
    return graph
