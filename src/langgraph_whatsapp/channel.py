from langgraph_whatsapp.agent import Agent
from twilio.twiml.messaging_response import MessagingResponse
from fastapi import Request, HTTPException
from twilio.request_validator import RequestValidator
from src.langgraph_whatsapp.config import TWILIO_AUTH_TOKEN
from abc import ABC, abstractmethod


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
        media_urls = []
        media_content_types = []
        
        for i in range(num_media):
            media_url = form_data.get(f'MediaUrl{i}', "")
            media_content_type = form_data.get(f'MediaContentType{i}', "")
            if media_url:
                media_urls.append(media_url)
                media_content_types.append(media_content_type)

        if not sender:
             raise HTTPException(status_code=400, detail="Missing 'From' in request form")

        agent_response = await self._process_message(sender, content, media_urls, media_content_types)

        twilio_resp = MessagingResponse()
        twilio_resp.message(agent_response)

        return str(twilio_resp)

    async def _process_message(self, sender: str, content: str, media_urls: list = None, media_content_types: list = None) -> str:
        """
        Process the incoming message and generate a response using the agent.

        :param sender: The sender's identifier (e.g., WhatsApp number)
        :param content: The content of the message
        :param media_urls: List of media URLs if present in the message
        :param media_content_types: List of media content types if present in the message
        :return: Response string from the agent
        """
        input_data = {
            "id": sender,
            "user_message": content,
        }
        
        # Add media information if available
        if media_urls and len(media_urls) > 0:
            input_data["media"] = [
                {"url": url, "content_type": content_type} 
                for url, content_type in zip(media_urls, media_content_types)
            ]
            
        print(input_data)
        # Invoke the agent with the message content and any media attachments
        return await self.agent.invoke(**input_data)