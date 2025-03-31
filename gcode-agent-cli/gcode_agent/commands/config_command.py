import os
import sys
import json

# Constants
AGENT_DIR = ".gcode-agent"
CONFIG_FILE = "config.json"
CONFIG_PATH = os.path.join(AGENT_DIR, CONFIG_FILE)

# Define allowed keys that can be set (to prevent arbitrary additions)
# Add more keys as needed (e.g., 'last_completed_step')
ALLOWED_CONFIG_KEYS = ["model", "current_step"]

def read_config():
    """Reads the configuration file."""
    if not os.path.exists(CONFIG_PATH):
        return None # Return None if config doesn't exist
    try:
        with open(CONFIG_PATH, 'r') as f:
            return json.load(f)
    except (IOError, json.JSONDecodeError) as e:
        print(f"Error reading configuration file '{CONFIG_PATH}': {e}", file=sys.stderr)
        return None

def write_config(config_data):
    """Writes the configuration data to the file."""
    try:
        # Ensure the .gcode-agent directory exists (though init should create it)
        os.makedirs(AGENT_DIR, exist_ok=True)
        with open(CONFIG_PATH, 'w') as f:
            json.dump(config_data, f, indent=4)
        return True
    except IOError as e:
        print(f"Error writing configuration file '{CONFIG_PATH}': {e}", file=sys.stderr)
        return False

def handle_config(args):
    """Handles the config command actions."""
    config_data = read_config()

    if config_data is None and args.config_action != 'set': # Allow set even if file doesn't exist
         if not os.path.exists(AGENT_DIR):
             print(f"Error: Project not initialized. Run 'gcode-agent init <spec_dir>' first.", file=sys.stderr)
         else:
             print(f"Error: Configuration file '{CONFIG_PATH}' not found or corrupted.", file=sys.stderr)
         return False

    action = args.config_action

    if action == "list":
        if config_data:
            print("Current configuration:")
            for key, value in config_data.items():
                print(f"  {key}: {value}")
        else:
             print("No configuration found.")
        return True

    elif action == "get":
        key = args.key
        if config_data and key in config_data:
            print(f"{key}: {config_data[key]}")
            return True
        else:
            print(f"Error: Key '{key}' not found in configuration.", file=sys.stderr)
            return False

    elif action == "set":
        key = args.key
        value = args.value

        if key not in ALLOWED_CONFIG_KEYS:
            print(f"Error: Setting key '{key}' is not allowed. Allowed keys: {ALLOWED_CONFIG_KEYS}", file=sys.stderr)
            return False

        if config_data is None:
             config_data = {} # Initialize if file didn't exist

        # Basic type guessing (can be improved)
        original_value = config_data.get(key)
        try:
            # Attempt to convert to int or float if possible
            if value.isdigit():
                parsed_value = int(value)
            elif '.' in value:
                 try:
                     parsed_value = float(value)
                 except ValueError:
                     parsed_value = value # Keep as string if float conversion fails
            # Handle booleans
            elif value.lower() in ['true', 'false']:
                parsed_value = value.lower() == 'true'
            # Handle null/none
            elif value.lower() in ['null', 'none']:
                 parsed_value = None
            else:
                parsed_value = value
        except ValueError:
            parsed_value = value # Keep as string if conversions fail

        config_data[key] = parsed_value
        if write_config(config_data):
            print(f"Set '{key}' to '{parsed_value}'")
            return True
        else:
            # Revert if write failed?
            # For simplicity, we don't revert here, but write_config should print error.
            return False
    else:
        # Should not happen due to argparse config
        print(f"Error: Unknown config action '{action}'", file=sys.stderr)
        return False
