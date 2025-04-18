from langgraph_whatsapp.agent import Agent
from twilio.twiml.messaging_response import MessagingResponse
from fastapi import Request, HTTPException
from twilio.request_validator import RequestValidator
from src.langgraph_whatsapp.config import TWILIO_AUTH_TOKEN, TWILIO_ACCOUNT_SID
from abc import ABC, abstractmethod
import logging
import requests
import base64
import mimetypes

LOGGER = logging.getLogger(__name__)


def twilio_url_to_data_uri(url: str) -> str:
    """Download the Twilio media and return a base‑64 data URI."""
    sid = TWILIO_ACCOUNT_SID
    token = TWILIO_AUTH_TOKEN
    if not sid or not token:
        raise RuntimeError("Twilio credentials are not configured")

    res = requests.get(url, auth=(sid, token), timeout=15)
    res.raise_for_status()
    mime = mimetypes.guess_type(url)[0] or "image/jpeg"
    data = base64.b64encode(res.content).decode()
    return f"data:{mime};base64,{data}"

class WhatsAppAgent(ABC):
    """
    Interface for WhatsApp agent implementations.
    All WhatsApp channel implementations should inherit from this class.
    """

    @abstractmethod
    async def handle_message(self, request: Request) -> str:
        """
        Entrypoint for handling incoming WhatsApp messages.
        
        :param request: The incoming request object
        :return: Response to be sent back to WhatsApp
        """
        pass

    @abstractmethod
    async def validate_request(self, request: Request) -> bool:
        """
        Validate the incoming request authenticity.
        
        :param request: The incoming request object
        :return: True if request is valid, False otherwise
        """
        pass

class WhatsAppAgentTwilio(WhatsAppAgent):
    def __init__(self):
        if not TWILIO_AUTH_TOKEN:
            raise ValueError("TWILIO_AUTH_TOKEN is not configured or empty.")
        if not TWILIO_ACCOUNT_SID:
             raise ValueError("TWILIO_ACCOUNT_SID is not configured or empty.")
        self.agent = Agent()
        self.validator = RequestValidator(TWILIO_AUTH_TOKEN)

    async def validate_request(self, request: Request) -> bool:
        """
        Validate the Twilio signature in the request.
        
        :param request: The incoming FastAPI request object
        :return: True if validation succeeds, False otherwise
        """
        form_data = await request.form()
        post_vars = dict(form_data)

        # Construct the URL using the forwarded headers to match what Twilio expects
        forwarded_proto = request.headers.get("x-forwarded-proto", "http")
        forwarded_host = request.headers.get("x-forwarded-host", request.headers.get("host", "localhost"))
        url = f"{forwarded_proto}://{forwarded_host}{request.url.path}"
        signature_header = request.headers.get("X-Twilio-Signature", "")

        return self.validator.validate(
            url,
            post_vars,
            signature_header
        )

    async def handle_message(self, request: Request) -> str:
        """
        Entrypoint for handling incoming WhatsApp messages with Twilio validation.

        :param request: The incoming FastAPI request object
        :return: Response containing TwiML XML or error
        """
        # Validate the request
        if not await self.validate_request(request):
            raise HTTPException(status_code=403, detail="Twilio signature validation failed")

        form_data = await request.form()
        sender = form_data.get('From', "").strip() # e.g., 'whatsapp:+14155238886'
        content = form_data.get('Body', "").strip()
        
        # Get media information if available
        num_media = int(form_data.get('NumMedia', "0"))
        
        # Initialize media as None
        media = None
        
        # If there's at least one media item and it's an image, use only the first one
        if num_media > 0:
            media_url = form_data.get('MediaUrl0', "")
            media_content_type = form_data.get('MediaContentType0', "")
            
            if media_url and media_content_type:
                if media_content_type.startswith('image/'):
                    # Only process images
                    try:
                        LOGGER.info(f"Found image: {media_url}. Converting to data URI...")
                        data_uri = twilio_url_to_data_uri(media_url)
                        media = {
                            "url": media_url,
                            "data_uri": data_uri,
                            "content_type": media_content_type
                        }
                        LOGGER.info(f"Successfully converted image to data URI.")
                    except Exception as e:
                         LOGGER.error(f"Failed to download or convert image {media_url}: {e}")
                         # Optionally decide if you want to proceed without media or raise error
                         media = None # Set media to None if conversion fails
                else:
                    LOGGER.warning(f"Ignoring non-image media type: {media_content_type}")
                
                # Log if additional media is being ignored
                if num_media > 1:
                    LOGGER.info(f"Ignoring {num_media-1} additional media items")

        if not sender:
             raise HTTPException(status_code=400, detail="Missing 'From' in request form")

        agent_response = await self._process_message(sender, content, media)

        twilio_resp = MessagingResponse()
        twilio_resp.message(agent_response)

        return str(twilio_resp)

    async def _process_message(self, sender: str, content: str, media: dict = None) -> str:
        """
        Process the incoming message and generate a response using the agent.

        :param sender: The sender's identifier (e.g., WhatsApp number)
        :param content: The content of the message
        :param media: Dictionary with image media data (url, data_uri, and content_type)
        :return: Response string from the agent
        """
        input_data = {
            "id": sender,
            "user_message": content,
        }
        
        # Add media information if available
        if media and "data_uri" in media:
            input_data["image"] = {
                 "image_url": {"url": media["data_uri"]},
            }
            
        print(f"Sending to agent: {input_data}")
        # Invoke the agent with the message content and image attachment
        return await self.agent.invoke(**input_data)