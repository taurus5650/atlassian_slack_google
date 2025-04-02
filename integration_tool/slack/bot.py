import ssl
from typing import Any, List, Union, Optional

import certifi
from slack_sdk import WebClient

from configuration.account import SlackBotConfig
from utility import logger, log_class
from .message_builder import MessageBuilderMethod


@log_class
class SlackBot:

    def __init__(self, token: Optional[str] = None):
        self.token = token or SlackBotConfig.SLACK_BOT_TOKEN

        if not self.token:
            raise ValueError("Bot token is required but not provided and no default exists")

        ssl_context = ssl.create_default_context(cafile=certifi.where())
        self.client = WebClient(token=self.token, ssl=ssl_context)
        self.message_builder = MessageBuilderMethod


    def chat_post_message(self,  channels: Union[str, List[str]], message: Any, message_builder_method: str = 'customize'):
        """ Send message to slack channel. """
        processed_message = getattr(self.message_builder, message_builder_method)(message)

        results = []
        for channel in channels:
            logger.info(f"Sending message to channel: {channel}")
            response = self.client.chat_postMessage(
                channel=channel,
                **processed_message,
            )
            results.append(response)

        logger.info(f"Successfully sent messages to {len(results)} channels")
        return results

    def channels_set_topic(self, channels: Union[str, List[str]], topic: str):
        """ Set the channel topic on top. """
        results = []
        for channel in channels:
            logger.info(f"Setting topic for channel {channel}: {topic}")
            response = self.client.conversations_setTopic(
                channel=channel,
                topic=topic
            )
            results.append(response)

        logger.info(f"Set topic for {len(results)} channels")
        return results

    def get_channel_info(self, channel: str):
        response = self.client.conversations_info(channel=channel)
        return response
