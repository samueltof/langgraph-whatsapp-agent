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

    async def invoke(self, id: str, user_message: str, image: dict = None) -> dict:
        """
        Process a user message through the LangGraph client.
        
        Args:
            id: The unique identifier for the conversation
            user_message: The message content from the user
            image: Dictionary with image data structured as {"image_url": {"url": data_uri}}.
                  The URL should be a data URI.
            
        Returns:
            dict: The result from the LangGraph run
        """
        print(f"Invoking agent with thread_id: {id}, message: {user_message}")

        try:
            message_content = []

            if user_message:
                message_content.append({
                    "type": "text",
                    "text": user_message
                })

            if image and isinstance(image, dict):
                # Add the image content directly, assuming it's pre-formatted
                message_content.append({
                    "type": "image_url",
                    "image_url": image["image_url"]
                })
                LOGGER.info(f"Added image data URI.")
            
            # Ensure content is not empty; default to user_message if only image was sent
            if not message_content and not user_message:
                # Handle cases where maybe only an image is sent without text
                # This might need specific handling depending on the graph requirements
                # For now, we'll proceed, but the graph must handle empty user messages
                LOGGER.warning("No text message provided, only image.")
            
            # If message_content is empty after processing, use user_message as fallback
            # This covers the case where only text is sent, and no image
            content_to_send = message_content if message_content else user_message

            request_payload = {
                "thread_id": str(uuid.uuid5(uuid.NAMESPACE_DNS, id)),
                "assistant_id": config.ASSISTANT_ID,
                "input": {
                    "messages": [
                        {
                            "role": "user",
                            "content": content_to_send
                        }
                    ]
                },
                "config": self.graph_config,
                "metadata": {
                    "event": "api_call",
                },
                "multitask_strategy": "interrupt",
                "if_not_exists": "create",
                "stream_mode": "values",
            }
            
            LOGGER.debug(f"Request payload: {json.dumps(request_payload, indent=2)}")
            
            async for chunk in self.client.runs.stream(
                **request_payload
            ):
                final_response = chunk
            return final_response.data["messages"][-1]["content"]
        except Exception as e:
            LOGGER.error(f"Error during invoke: {str(e)}", exc_info=True)
            raise