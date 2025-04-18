# channel.py
import base64, logging, mimetypes, requests
from abc import ABC, abstractmethod

from fastapi import Request, HTTPException
from twilio.twiml.messaging_response import MessagingResponse

from src.langgraph_whatsapp.agent import Agent
from src.langgraph_whatsapp.config import TWILIO_AUTH_TOKEN, TWILIO_ACCOUNT_SID

LOGGER = logging.getLogger("whatsapp")


# ---------------------------------------------------------------------
def twilio_url_to_data_uri(url: str) -> str:
    """Download the Twilio media URL and convert to data‑URI (base64)."""
    if not (TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN):
        raise RuntimeError("Twilio credentials are missing")

    resp = requests.get(url, auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN), timeout=20)
    resp.raise_for_status()

    mime = mimetypes.guess_type(url)[0] or "application/octet-stream"
    b64  = base64.b64encode(resp.content).decode()
    return f"data:{mime};base64,{b64}"


# ---------------------------------------------------------------------
class WhatsAppAgent(ABC):
    @abstractmethod
    async def handle_message(self, request: Request) -> str: ...


class WhatsAppAgentTwilio(WhatsAppAgent):
    def __init__(self) -> None:
        if not (TWILIO_AUTH_TOKEN and TWILIO_ACCOUNT_SID):
            raise ValueError("Twilio credentials are not configured")
        self.agent = Agent()

    # --------------------------------------------------------------
    async def handle_message(self, request: Request) -> str:
        form = await request.form()

        # Ignore delivery‑status callbacks (no From / Body)
        if "MessageStatus" in form and "SmsSid" in form:
            LOGGER.info("Delivery callback received → 200 OK, no action")
            return "<Response></Response>"

        sender  = form.get("From", "").strip()
        content = form.get("Body", "").strip()
        if not sender:
            raise HTTPException(400, detail="Missing 'From' in request form")

        # Collect ALL images (you’ll forward only the first one for now)
        images = []
        for i in range(int(form.get("NumMedia", "0"))):
            url   = form.get(f"MediaUrl{i}", "")
            ctype = form.get(f"MediaContentType{i}", "")
            if url and ctype.startswith("image/"):
                try:
                    images.append({
                        "url": url,
                        "data_uri": twilio_url_to_data_uri(url),
                        "content_type": ctype
                    })
                except Exception as err:
                    LOGGER.error("Failed to download %s: %s", url, err)

        # Assemble payload for the LangGraph agent
        input_data = {
            "id": sender,
            "user_message": content,
        }
        if images:
            # Pass just the first image for now; adapt if you support more
            input_data["image"] = {
                "image_url": {"url": images[0]["data_uri"]}
            }

        LOGGER.info("Invoking agent with: %s", {k: v for k, v in input_data.items()
                                               if k != 'image'})

        reply = await self.agent.invoke(**input_data)

        twiml = MessagingResponse()
        twiml.message(reply)
        return str(twiml)
