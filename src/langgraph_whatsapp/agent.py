import logging
from langgraph_sdk import get_client
from langgraph_whatsapp import config
import json
import uuid

LOGGER = logging.getLogger(__name__)


class Agent:
    def __init__(self):
        self.client = get_client(url=config.LANGGRAPH_URL)
        try:
            self.graph_config = (
                json.loads(config.CONFIG) if isinstance(config.CONFIG, str) else config.CONFIG
            )
        except json.JSONDecodeError as e:
            LOGGER.error(f"Failed to parse CONFIG as JSON: {e}")
            raise

    async def invoke(self, id: str, user_message: str, images: list = None) -> dict:
        """
        Process a user message through the LangGraph client.
        
        Args:
            id: The unique identifier for the conversation
            user_message: The message content from the user
            images: List of dictionaries with image data
            
        Returns:
            dict: The result from the LangGraph run
        """
        LOGGER.info(f"Invoking agent with thread_id: {id}")

        try:
            # Build message content - always use a list for consistent format
            message_content = []
            if user_message:
                message_content.append({
                    "type": "text",
                    "text": user_message
                })

            if images:
                for img in images:
                    if isinstance(img, dict) and "image_url" in img:
                        message_content.append({
                            "type": "image_url",
                            "image_url": img["image_url"]
                        })
            
            request_payload = {
                "thread_id": str(uuid.uuid5(uuid.NAMESPACE_DNS, id)),
                "assistant_id": config.ASSISTANT_ID,
                "input": {
                    "messages": [
                        {
                            "role": "user",
                            "content": message_content
                        }
                    ]
                },
                "config": self.graph_config,
                "metadata": {"event": "api_call"},
                "multitask_strategy": "interrupt",
                "if_not_exists": "create",
                "stream_mode": "values",
            }
            
            final_response = None
            async for chunk in self.client.runs.stream(**request_payload):
                final_response = chunk
            
            # Enhanced response handling for different formats
            LOGGER.info(f"Raw response type: {type(final_response)}")
            LOGGER.info(f"Raw response data: {final_response.data if hasattr(final_response, 'data') else 'No data attr'}")
            
            # Try different response formats based on what the deployed agent returns
            try:
                # Original format - try first
                return final_response.data["messages"][-1]["content"]
            except (KeyError, TypeError, IndexError) as e:
                LOGGER.info(f"Original format failed: {e}, trying alternative formats...")
                
                # Try alternative response formats
                if hasattr(final_response, 'data') and final_response.data:
                    data = final_response.data
                    
                    # Format 1: Direct content in data
                    if isinstance(data, str):
                        return data
                    
                    # Format 2: Content in different message structure
                    if isinstance(data, dict):
                        # Check for direct content field
                        if "content" in data:
                            return data["content"]
                        
                        # Check for output field
                        if "output" in data:
                            output = data["output"]
                            if isinstance(output, str):
                                return output
                            elif isinstance(output, dict) and "content" in output:
                                return output["content"]
                        
                        # Check for response field
                        if "response" in data:
                            response = data["response"]
                            if isinstance(response, str):
                                return response
                        
                        # Check for assistant message in messages array
                        if "messages" in data and isinstance(data["messages"], list):
                            messages = data["messages"]
                            # Look for assistant messages
                            for msg in reversed(messages):
                                if isinstance(msg, dict) and msg.get("role") == "assistant":
                                    content = msg.get("content")
                                    if content:
                                        return content if isinstance(content, str) else str(content)
                            
                            # If no assistant message, get the last message
                            if messages:
                                last_msg = messages[-1]
                                if isinstance(last_msg, dict) and "content" in last_msg:
                                    return last_msg["content"]
                        
                        # Format 3: Look for any content-like field
                        for key in ["text", "message", "reply", "answer"]:
                            if key in data:
                                return str(data[key])
                    
                    # Last resort: return the entire data as string
                    return str(data)
                
                # If no data attribute, return the response as string
                return str(final_response)
                
        except Exception as e:
            LOGGER.error(f"Error during invoke: {str(e)}", exc_info=True)
            raise
    