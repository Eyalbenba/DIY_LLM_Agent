import logging
from logging.handlers import RotatingFileHandler
import os

class ScraperLogger:
    def __init__(self, log_file='scraper_log.txt', log_dir='logs', level=logging.INFO,log_to_console=False):
        """
        Initialize a logger for the scraping process.

        :param log_file: Name of the log file.
        :param log_dir: Directory where the log file will be saved.
        :param level: Logging level.
        """
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(level)
        self.log_dir=log_dir
        # Check if handlers already exist
        if not self.logger.handlers:
            # Define the log format
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

            # Create log directory if it doesn't exist
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)

            # File handler for rotating logs
            file_handler = RotatingFileHandler(
                os.path.join(log_dir, log_file),
                maxBytes=5 * 1024 * 1024,
                backupCount=5
            )
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

            # Console handler
            if log_to_console:
              console_handler = logging.StreamHandler()
              console_handler.setFormatter(formatter)
              self.logger.addHandler(console_handler)

    def get_logger(self):
        return self.logger


