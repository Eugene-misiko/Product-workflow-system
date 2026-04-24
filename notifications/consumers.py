import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer

logger = logging.getLogger(__name__)

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope.get("user")

         #Check if user exists and is authenticated
        if not self.user or self.user.is_anonymous:
            logger.warning("WebSocket connection rejected: Anonymous User")
            await self.close()
            return

        #Get company_id (with fallback to avoid crashes)
        company_id = getattr(self.user, "company_id", None)
        
        if not company_id:
            logger.warning(f"WebSocket rejected: User {self.user.id} has no company_id")
            await self.close()
            return

        self.group_name = f"payments_{company_id}"

        # Join the group
        try:
            await self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )
            await self.accept()
            logger.info(f"WebSocket connected: User {self.user.id} joined {self.group_name}")
            
        except Exception as e:
            logger.error(f"Failed to join group: {str(e)}")
            await self.close()

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )
            logger.info(f"WebSocket disconnected: {self.group_name}")

    async def send_notification(self, event):
        """
        Expects event['data'] to be a dictionary.
        This matches your React frontend JSON.parse logic.
        """
        try:
            await self.send(text_data=json.dumps(event["data"]))
        except Exception as e:
            logger.error(f"Error sending WebSocket message: {e}")
