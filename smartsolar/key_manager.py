"""
Shared key management functions for SmartSolar BLE data collection.
"""
import json
import os
import logging

logger = logging.getLogger(__name__)

KEYS_FILE = "/data/smartsolar-keys.json"

def load_device_keys():
    """Load device encryption keys from file or environment variables."""
    device_keys = {}
    
    # First, try to load from JSON file
    if os.path.exists(KEYS_FILE):
        try:
            with open(KEYS_FILE, 'r') as f:
                keys_data = json.load(f)
                device_keys = keys_data.get('devices', {})
                logger.info(f"Loaded {len(device_keys)} device key(s) from {KEYS_FILE}")
        except Exception as e:
            logger.error(f"Error loading keys from {KEYS_FILE}: {e}")
    
    # Then, check environment variables (these override file settings)
    # Format: SMARTSOLAR_KEY_<MAC_ADDRESS> where MAC address has colons replaced with underscores
    for key, value in os.environ.items():
        if key.startswith('SMARTSOLAR_KEY_'):
            mac_address = key.replace('SMARTSOLAR_KEY_', '').replace('_', ':')
            device_keys[mac_address] = value
            logger.info(f"Loaded key for {mac_address} from environment variable")
    
    return device_keys

def save_device_keys(device_keys):
    """Save device encryption keys to file."""
    try:
        from datetime import datetime
        keys_data = {
            'devices': device_keys,
            'updated': datetime.utcnow().isoformat()
        }
        with open(KEYS_FILE, 'w') as f:
            json.dump(keys_data, f, indent=2)
        logger.info(f"Saved {len(device_keys)} device key(s) to {KEYS_FILE}")
        return True
    except Exception as e:
        logger.error(f"Error saving keys to {KEYS_FILE}: {e}")
        return False

def parse_victron_data(parsed_obj):
    """Convert Victron parsed data object to dictionary."""
    parsed_dict = {}
    try:
        # The actual data is in the _data attribute
        if hasattr(parsed_obj, '_data') and isinstance(parsed_obj._data, dict):
            # Extract the data dictionary
            data = parsed_obj._data
            # Convert enum values to strings
            for key, value in data.items():
                if hasattr(value, 'name'):  # It's an enum
                    parsed_dict[key] = value.name
                else:
                    parsed_dict[key] = value
            
            # Add model ID if available
            if hasattr(parsed_obj, '_model_id'):
                parsed_dict['model_id'] = parsed_obj._model_id
        else:
            # Fallback to vars
            parsed_dict = vars(parsed_obj)
    except Exception as e:
        logger.error(f"Error extracting data: {e}")
        # If that fails, try accessing known attributes
        for attr in dir(parsed_obj):
            if not attr.startswith('_'):
                try:
                    value = getattr(parsed_obj, attr)
                    # Skip methods
                    if not callable(value):
                        if hasattr(value, 'name'):  # It's an enum
                            parsed_dict[attr] = value.name
                        else:
                            parsed_dict[attr] = value
                except:
                    pass
    
    return parsed_dict 