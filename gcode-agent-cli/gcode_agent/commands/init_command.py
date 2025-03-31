import os
import shutil
import sys
import json

AGENT_DIR = ".gcode-agent"
SPEC_SUBDIR = "spec"
OUTPUT_SUBDIR = "outputs"
CONFIG_FILE = "config.json"

def handle_init(args):
    """Handles the initialization of the gcode-agent project."""
    source_spec_dir = args.spec_dir
    verbose = args.verbose

    if not os.path.isdir(source_spec_dir):
        print(f"Error: Specification directory not found: {source_spec_dir}", file=sys.stderr)
        return False # Indicate failure

    if os.path.exists(AGENT_DIR):
        overwrite = input(f"Directory '{AGENT_DIR}' already exists. Overwrite? (y/N): ").lower()
        if overwrite != 'y':
            print("Initialization cancelled.")
            return True # Indicate success (cancelled)
        else:
            try:
                if verbose:
                    print(f"Removing existing directory: {AGENT_DIR}")
                shutil.rmtree(AGENT_DIR)
            except OSError as e:
                print(f"Error removing existing directory '{AGENT_DIR}': {e}", file=sys.stderr)
                return False

    target_spec_dir = os.path.join(AGENT_DIR, SPEC_SUBDIR)
    target_output_dir = os.path.join(AGENT_DIR, OUTPUT_SUBDIR)

    try:
        if verbose:
            print(f"Creating agent directory: {AGENT_DIR}")
        os.makedirs(AGENT_DIR, exist_ok=True)

        if verbose:
            print(f"Copying spec files from {source_spec_dir} to {target_spec_dir}")
        shutil.copytree(source_spec_dir, target_spec_dir)

        # Create the outputs directory
        if verbose:
            print(f"Creating outputs directory: {target_output_dir}")
        os.makedirs(target_output_dir, exist_ok=True)

        # Create a basic config file
        config_path = os.path.join(AGENT_DIR, CONFIG_FILE)
        config_data = {
            "source_spec_directory": os.path.abspath(source_spec_dir),
            "current_step": None, # Track generation progress later
            "model": args.model # Store the model used during init
        }
        if verbose:
            print(f"Creating config file: {config_path}")
        with open(config_path, 'w') as f:
            json.dump(config_data, f, indent=4)

        print(f"gcode-agent initialized successfully in '{AGENT_DIR}'")
        print(f"Specifications copied from: {source_spec_dir}")
        return True # Indicate success

    except OSError as e:
        print(f"Error during initialization: {e}", file=sys.stderr)
        # Clean up partially created directory if error occurred
        if os.path.exists(AGENT_DIR):
            try:
                shutil.rmtree(AGENT_DIR)
            except OSError as cleanup_e:
                print(f"Error during cleanup: {cleanup_e}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"An unexpected error occurred during initialization: {e}", file=sys.stderr)
        # Clean up partially created directory if error occurred
        if os.path.exists(AGENT_DIR):
             try:
                 shutil.rmtree(AGENT_DIR)
             except OSError as cleanup_e:
                 print(f"Error during cleanup: {cleanup_e}", file=sys.stderr)
        return False
