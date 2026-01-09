import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler

class LoggingService:
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LoggingService, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.setup_logging()
            LoggingService._initialized = True
    
    def setup_logging(self):
        """Setup logging configuration with file output"""
        # Create logs directory if it doesn't exist
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        
        # Clear existing handlers
        root_logger.handlers.clear()
        
        # File handler with rotation
        log_file = os.path.join(log_dir, 'hrms_ai.log')
        file_handler = RotatingFileHandler(
            log_file, 
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)
        
        # Set specific logger levels
        logging.getLogger('hrms_ai.services.hybrid_search_engine').setLevel(logging.INFO)
        logging.getLogger('hrms_ai.services.ai_search_service').setLevel(logging.INFO)
        
        print(f"Logging configured - File: {log_file}")

# Initialize logging when module is imported
logging_service = LoggingService()