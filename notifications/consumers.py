import json
from channels.generic.websocket import AsyncWebsocketConsumer

class NotificationConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        user = self.scope.get("user")

        if not user or user.is_anonymous:
            await self.close()
            return

        self.group_name = f"payments_{user.company_id}"

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        group = getattr(self, "group_name", None)
        if group:
            await self.channel_layer.group_discard(
                group,
                self.channel_name
            )

    async def send_notification(self, event):
        await self.send(text_data=json.dumps(event["data"]))