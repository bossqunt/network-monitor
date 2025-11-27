"""
Configuration loader module
"""
import yaml
import os
import logging

logger = logging.getLogger(__name__)


def load_config(config_path='config.yaml'):
    """Load configuration from YAML file"""
    if not os.path.exists(config_path):
        logger.error(f"Configuration file not found: {config_path}")
        return None
    
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        logger.info(f"Configuration loaded from {config_path}")
        return config
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        return None


def validate_config(config):
    """Validate configuration structure"""
    required_sections = ['database', 'ping', 'traceroute']
    
    for section in required_sections:
        if section not in config:
            logger.error(f"Missing required configuration section: {section}")
            return False
    
    # Validate database config
    db_config = config['database']
    required_db_fields = ['host', 'user', 'password', 'database']
    for field in required_db_fields:
        if field not in db_config:
            logger.error(f"Missing required database field: {field}")
            return False
    
    logger.info("Configuration validation passed")
    return True
