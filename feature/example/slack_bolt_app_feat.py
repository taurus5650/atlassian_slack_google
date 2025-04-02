from flask import Blueprint

from integration_tool import SlackBoltApp, SlackBot
from utility import logger, log_func

example_sbqf_route = Blueprint('example_sbqf_route', __name__)

slack_app = SlackBoltApp()
slack_app.start()
slack_bot = SlackBot()


@log_func
@slack_app.command('/ags_health_check"')
def handle_command(ack, command, say, client):
    try:
        logger.info(f"Received slash command: {command}")
        ack()
        command_text = command.get('text', '')
        user_id = command.get('user_id')
        channel_id = command.get('channel_id')

        logger.info(f"Command from user {user_id} in channel {channel_id}: '{command_text}'")
        say(f"<@{user_id}> AGS Happy Testing :)")

    except Exception as e:
        logger.error(f"Exception: {e}", exc_info=True)
