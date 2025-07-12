from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, MessagesState
from langgraph.prebuilt import ToolNode
from langchain_core.messages import HumanMessage, AIMessage
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

async def build_agent():
    """
    Ultra-simple agent build without external dependencies for basic testing.
    """
    print("ℹ️ Building ultra-simple agent for basic testing...")
    
    # Create the model
    model = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash-exp",
        temperature=0.7
    )
    
    # Define the chatbot function
    def chatbot(state: MessagesState):
        return {"messages": [model.invoke(state["messages"])]}
    
    # Create a simple graph
    graph_builder = StateGraph(MessagesState)
    graph_builder.add_node("chatbot", chatbot)
    graph_builder.set_entry_point("chatbot")
    graph_builder.set_finish_point("chatbot")
    
    graph = graph_builder.compile()
    
    print("✅ Ultra-simple agent built successfully - ready for basic conversations!")
    return graph 