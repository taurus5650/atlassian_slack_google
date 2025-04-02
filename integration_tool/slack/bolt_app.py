import threading
import time
from typing import Optional, Callable

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from configuration.account import SlackBotConfig
from utility import logger, log_class, set_correlation_id


@log_class
class SlackBoltApp:
    def __init__(self, bot_token: Optional[str] = None, app_token: Optional[str] = None,
                 signing_secret: Optional[str] = None):
        self.bot_token = bot_token or SlackBotConfig.SLACK_BOT_TOKEN
        self.app_token = app_token or SlackBotConfig.SLACK_APP_TOKEN
        self.signing_secret = signing_secret or SlackBotConfig.SLACK_SIGNING_SECRET

        if not self.bot_token:
            raise ValueError("Bot token is required but not provided and no default exists")

        self.app = App(token=self.bot_token, signing_secret=self.signing_secret)
        self._setup_handlers()
        self.handler = None
        self._thread = None
        self._is_running = False

    def _setup_handlers(self):
        """ Set up handlers for the Slack Bolt app. """
        @self.app.error
        def global_error_handler(error, body, logger):
            logger.error(f"Error: {error}")
            logger.debug(f"Request body: {body}")

        @self.app.event('message')
        def handle_message_events(body, logger):
            logger.info(f"message: {body}")

        @self.app.event('reaction_added')
        def handle_reaction_added_events(body, logger):
            logger.info(f"reaction_added: {body}")

        @self.app.event('reaction_removed')
        def handle_reaction_removed_events(body, logger):
            logger.info(f"reaction_removed: {body}")

        @self.app.event('emoji_changed')
        def handle_emoji_events(body, logger):
            logger.info(f"emoji_changed: {body}")

    def __enter__(self):
        """ Support for context manager protocol. """
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """ Clean up resources when exiting context. """
        self.stop()
        return False  # Don't suppress exceptions

    def start(self, start_socket_mode: bool = True) -> 'SlackBoltApp':
        """ Start the Slack Bolt application. """
        if self._is_running:
            logger.warning('Slack Bot application is already running')
            return self

        if start_socket_mode:
            self._start_socket_mode()

        return self

    def _start_socket_mode(self):
        """ Start the application in Socket Mode. """
        if not self.app_token:
            raise ValueError('App token is required for Socket Mode')

        try:
            self.handler = SocketModeHandler(app=self.app, app_token=self.app_token)
            self._thread = threading.Thread(target=self.handler.start, daemon=True)
            self._thread.start()

            connection_timeout = 5  # seconds
            start_time = time.time()
            while time.time() - start_time < connection_timeout:
                if self._thread.is_alive():
                    self._is_running = True
                    logger.info("Socket Mode connection established")
                    break
                time.sleep(0.1)

            if not self._is_running:
                logger.warning('_start_socket_mode connection may not be established correctly')
        except Exception as e:
            logger.error(f"Failed to start Socket Mode: {e}")
            raise

    def stop(self):
        """ Stop the Slack Bolt application and clean up resources. """
        if not self._is_running:
            logger.warning("Slack Bot application is not running")
            return

        logger.info("Stopping the Slack Bot application...")

        # Implement proper shutdown
        if self.handler:
            # Bolt doesn't have a clean way to stop the socket mode handler
            self._is_running = False
            self.handler = None

        if self._thread and self._thread.is_alive():
            self._thread = None

        logger.info("Slack Bot application stopped")

    def action(self, action_id: str, *args, **kwargs) -> Callable:
        """ Register an action handler. """
        return self.app.action(action_id, *args, **kwargs)

    def message(self, *args, **kwargs) -> Callable:
        """  Register a new message event listener. """
        return self.app.message(*args, **kwargs)

    def event(self, event_type: str, *args, **kwargs) -> Callable:
        """ Register an event listener. """
        return self.app.event(event_type, *args, **kwargs)

    def command(self, command_name: str, *args, **kwargs) -> Callable:
        """ Register a slash command handler."""
        return self.app.command(command_name, *args, **kwargs)
