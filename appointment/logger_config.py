# logger_config.py
# Path: appointment/logger_config.py

"""
Author: Adams Pierre David
Since: 1.1.0
"""

import logging
import sys
from datetime import datetime

import colorama

# Initialize colorama for cross-platform color support
colorama.init()


class ColoredFormatter(logging.Formatter):
    COLORS = {
        'DEBUG': colorama.Fore.BLUE,
        'INFO': colorama.Fore.GREEN,
        'WARNING': colorama.Fore.YELLOW,
        'ERROR': colorama.Fore.RED,
        'CRITICAL': colorama.Fore.RED + colorama.Style.BRIGHT,
    }

    def format(self, record):
        log_color = self.COLORS.get(record.levelname, colorama.Fore.WHITE)
        log_time = datetime.fromtimestamp(record.created).strftime('%d/%b/%Y %H:%M:%S')

        log_msg = (
            f"{log_color}[{log_time}] {record.levelname:<4}{colorama.Style.RESET_ALL} "
            f"{colorama.Fore.LIGHTBLUE_EX}{record.name}:{record.funcName}:{record.lineno}{colorama.Style.RESET_ALL} "
            f"- {record.getMessage()}"
        )

        if record.exc_info:
            log_msg += '\n' + self.formatException(record.exc_info)
        return log_msg


def get_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Create a colored formatter
    formatter = ColoredFormatter()

    # Create a stream handler
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.DEBUG)
    stream_handler.setFormatter(formatter)

    # Add the handler to the logger
    logger.addHandler(stream_handler)

    return logger
