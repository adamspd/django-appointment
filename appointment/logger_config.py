# logger_config.py

import logging
import sys

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# configure basicConfig with the formatter, log level, and handlers
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p',
                    level=logging.DEBUG,
                    handlers=[logging.StreamHandler(sys.stdout)])
