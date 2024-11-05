# myapp/management/commands/test_channels.py

import asyncio
from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    help = 'Test if Django Channels is working properly'

    def handle(self, *args, **kwargs):
        # Check if Channels is configured
        if not hasattr(settings, 'CHANNEL_LAYERS'):
            self.stdout.write(self.style.ERROR('Channels is not configured in this application'))
            return

        # Run the async test function
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.test_channels())

    async def test_channels(self):
        try:
            from channels.layers import get_channel_layer
        except ImportError:
            self.stdout.write(self.style.ERROR('Django Channels is not installed'))
            return

        channel_layer = get_channel_layer()
        if not channel_layer:
            self.stdout.write(self.style.ERROR('Channels layer is not configured properly'))
            return

        test_channel = 'test_channel'
        test_message = {'type': 'test.message', 'text': 'Hello, Channels!'}

        try:
            # Send a message to the channel
            await channel_layer.send(test_channel, test_message)
            self.stdout.write(self.style.SUCCESS('Message sent to channel'))

            # Receive the message from the channel
            received_message = await channel_layer.receive(test_channel)
            self.stdout.write(self.style.SUCCESS(f'Message received from channel: {received_message}'))

            # Verify the message content
            if received_message['text'] == 'Hello, Channels!':
                self.stdout.write(self.style.SUCCESS('Channels test completed successfully'))
            else:
                self.stdout.write(self.style.ERROR('Channels test failed: Message content mismatch'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'An error occurred: {e}'))