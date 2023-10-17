# logger_config.py
# Path: appointment/logger_config.py

"""
Author: Adams Pierre David
Since: 1.1.0
"""

import logging
import sys

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# TODO: change the logger format configuration later
# configure basicConfig with the formatter, log level, and handlers
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG,
                    handlers=[logging.StreamHandler(sys.stdout)])
