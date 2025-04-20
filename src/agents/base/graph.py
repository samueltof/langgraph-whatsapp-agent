from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from langgraph_supervisor import create_supervisor
from contextlib import asynccontextmanager
from langchain_mcp_adapters.client import MultiServerMCPClient
from agents.base.prompt import CALENDAR_AGENT_PROMPT, SUPERVISOR_PROMPT
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

@asynccontextmanager
async def build_agent():

    servers = {}

    today = datetime.now().strftime("%Y-%m-%d")
 
    # Add MCP server URLs here for SSE transport.
    # Example:
    # servers["my_server"] = {
    #     "url": os.getenv("MY_SERVER_URL"),
    #     "transport": "sse"
    # }
    
    # Define available MCP server URLs
    mcp_servers = {
        "zapier": os.getenv("ZAPIER_URL_MCP"),
        "supermemory": os.getenv("SUPERMEMORY_URL_MCP")
    }
    
    # Add configured servers with SSE transport
    for server_name, url in mcp_servers.items():
        if url:
            servers[server_name] = {
                "url": url,
                "transport": "sse"
            }

    async with MultiServerMCPClient(servers) as client:

        calendar_agent = create_react_agent(
            model=ChatGoogleGenerativeAI(
                model="gemini-2.0-flash-exp",
            ),
            tools=client.get_tools(),
            name="calendar_agent",
            prompt=CALENDAR_AGENT_PROMPT.render(today=today)
        )

        graph = create_supervisor(
            [calendar_agent],
            model=ChatGoogleGenerativeAI(
                model="gemini-2.0-flash-exp",
            ),
            output_mode="last_message",
            prompt=SUPERVISOR_PROMPT.render()
        )
        
        yield graph
