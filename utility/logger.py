import contextvars
import logging
import uuid
from datetime import datetime, timezone, timedelta
from functools import wraps
from typing import Optional


class Logger:
    DEFAULT_FORMAT = "%(asctime)s | %(levelname)s | %(correlation_id)s | %(message)s"
    DEFAULT_LEVEL = logging.DEBUG

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, level: int = DEFAULT_LEVEL, log_format: str = DEFAULT_FORMAT):
        # Avoid to do initialize
        if getattr(self, '_initialized', False):
            return

        self._initialized = True
        self.uuid_var = contextvars.ContextVar("correlation_id", default=None)
        self._logger = logging.getLogger("AGSHub")
        self._level = level
        self._log_format = log_format
        self._setup_logger()

    def _setup_logger(self) -> None:
        if self._logger.hasHandlers():
            return

        self._logger.setLevel(self._level)
        context_filter = self._create_context_filter()

        handlers = [self._create_console_handler()]
        for handler in handlers:
            handler.addFilter(context_filter)
            self._logger.addHandler(handler)

    def _create_console_handler(self):
        console_handler = logging.StreamHandler()
        formatter = logging.Formatter(self._log_format)

        def converter(timestamp):
            conv_datetime = datetime.fromtimestamp(timestamp, tz=timezone(timedelta(hours=8)))
            return conv_datetime.timetuple()

        formatter.converter = converter
        console_handler.setFormatter(formatter)
        return console_handler

    def _create_context_filter(self):
        class ContextFilter(logging.Filter):
            def __init__(self, uuid_var):
                super().__init__()
                self.uuid_var = uuid_var

            def filter(self, record):
                record.correlation_id = self.uuid_var.get() or "NA"
                return True

        return ContextFilter(self.uuid_var)

    def set_correlation_id(self) -> str:
        """S et correlation id before request and return it. """
        correlation_id = str(uuid.uuid4())  # Generate new correlation ID
        self.uuid_var.set(correlation_id)  # Set it in the contextvar
        return correlation_id

    def get_correlation_id(self) -> Optional[str]:
        """ Get correlation id after request. """
        return self.uuid_var.get()

    def log_func(self, func):
        """Decorator for logging function calls"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                if self.uuid_var.get() is None:
                    self.set_correlation_id()

                func_name = func.__name__
                self._logger.info(f"○ Func start: {func_name}")

                result = func(*args, **kwargs)
                self._logger.info(f"● Func end: {func_name}")
                return result
            except Exception as e:
                self._logger.error(f"✘ Func ERROR: '{func.__name__}': {e}", exc_info=True)
                raise

        return wrapper

    def log_class(self, cls):
        """ Decorator for logging all methods in a class. """
        for attr in dir(cls):
            if callable(getattr(cls, attr)) and not attr.startswith("__"):
                setattr(cls, attr, self.log_func(getattr(cls, attr)))
        return cls

    def debug(self, msg, *args, **kwargs):
        return self._logger.debug(msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        return self._logger.info(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        return self._logger.warning(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        return self._logger.error(msg, *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        return self._logger.critical(msg, *args, **kwargs)

    def exception(self, msg, *args, **kwargs):
        return self._logger.exception(msg, *args, **kwargs)

    def __getattr__(self, name):
        if not hasattr(self, '_logger') or self._logger is None:
            raise AttributeError(f"Logger initialization incomplete, cannot access '{name}'")

        if hasattr(self._logger, name):
            return getattr(self._logger, name)

        raise AttributeError(f"'Logger' object has no attribute '{name}'")


logger = Logger()

log_func = logger.log_func
log_class = logger.log_class
set_correlation_id = logger.set_correlation_id
get_correlation_id = logger.get_correlation_id
uuid_var = logger.uuid_var