import configparser
import os

# Initialize the configuration parser.
config = configparser.ConfigParser()

# Locate the config.ini relative to this file.
config_path = os.path.join(os.path.dirname(__file__), '..', 'config.ini')
config.read(config_path)
default_config = config['DEFAULT']

# Global configuration values accessible throughout the package.
USER_AGENT = default_config.get('UserAgent')
MAX_RETRIES = default_config.getint('MaxRetries', fallback=3)
BASE_URL_UFC = default_config.get('BaseUrl_UFC')
BASE_URL_SHERDOG = default_config.get('BaseUrl_Sherdog')
BASE_URL_UFCSTATS = default_config.get('BaseUrl_UFCStats')
