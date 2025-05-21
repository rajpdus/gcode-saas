import os
import json
import sys
from argparse import Namespace # To help call handle_generate

# Assuming generate_command is in the same directory
from .generate_command import handle_generate, STEP_TEMPLATE_MAP 

AGENT_DIR = ".gcode-agent"
CONFIG_FILE = "config.json"
STEPS_SEQUENCE = ["step1", "step2", "step3", "step4", "step5", "step6"]

def handle_next_step(args, client):
    """Handles the execution of the next step in the project sequence."""
    config_path = os.path.join(AGENT_DIR, CONFIG_FILE)
    verbose = args.verbose if hasattr(args, 'verbose') else False

    if not os.path.exists(config_path):
        print(f"Error: Configuration file not found at {config_path}.", file=sys.stderr)
        print("Please run 'gcode-agent init <problem_description>' first.", file=sys.stderr)
        return False

    try:
        with open(config_path, 'r') as f:
            config_data = json.load(f)
    except Exception as e:
        print(f"Error reading configuration file: {e}", file=sys.stderr)
        return False

    current_project_step = config_data.get("current_project_step")

    if not current_project_step:
        print("Error: 'current_project_step' not found in config.json.", file=sys.stderr)
        print("Consider running 'gcode-agent init' or 'gcode-agent config set current_project_step step0'.", file=sys.stderr)
        return False

    if current_project_step == STEPS_SEQUENCE[-1]:
        print(f"All steps completed. Current step is '{current_project_step}'. Nothing to do.")
        return True

    next_step_name = ""
    if current_project_step == "step0": # Initial state
        next_step_name = STEPS_SEQUENCE[0]
    else:
        try:
            current_index = STEPS_SEQUENCE.index(current_project_step)
            next_step_name = STEPS_SEQUENCE[current_index + 1]
        except ValueError:
            print(f"Error: Current step '{current_project_step}' from config is not in the defined STEPS_SEQUENCE.", file=sys.stderr)
            print(f"Valid steps are: {STEPS_SEQUENCE}", file=sys.stderr)
            print("You might need to manually set it using 'gcode-agent config set current_project_step <valid_step>'.", file=sys.stderr)
            return False
        except IndexError:
            # This case should be caught by the check against STEPS_SEQUENCE[-1] earlier,
            # but as a safeguard:
            print(f"Error: Cannot determine next step after '{current_project_step}'. It seems to be the last step.", file=sys.stderr)
            return False
            
    if not next_step_name:
        print(f"Error: Could not determine next step after '{current_project_step}'.", file=sys.stderr)
        return False

    print(f"Current project step: '{current_project_step}'.")
    print(f"Executing next step: '{next_step_name}'...")

    # Prepare arguments for handle_generate
    # The `client` is passed directly to handle_next_step and then to handle_generate
    generate_args = Namespace(
        step=next_step_name,
        apply=args.apply if hasattr(args, 'apply') else False,
        verbose=verbose,
        model=config_data.get("model") # Use model from config, or allow override via args if 'next' supports it
        # Add other args if 'next' command needs to pass them or if handle_generate expects them
    )
    
    # Ensure client is passed to handle_generate
    # This assumes handle_generate's signature is (args, client)
    # If handle_generate doesn't expect client directly, this might need adjustment
    # based on refactoring in Step 5. For now, we assume it does.
    if client is None and verbose:
        print("Warning: Gemini client is None in handle_next_step.", file=sys.stderr)


    # Call handle_generate
    # This call assumes that handle_generate is suitably refactored or can accept args and client this way.
    # The actual refactoring of handle_generate is Step 5 of the plan.
    try:
        # Pass the client to handle_generate
        success = handle_generate(generate_args, client)
    except Exception as e:
        print(f"An error occurred while executing step '{next_step_name}': {e}", file=sys.stderr)
        success = False

    if success:
        print(f"Successfully completed step '{next_step_name}'.")
        # Update config
        config_data["current_project_step"] = next_step_name
        try:
            with open(config_path, 'w') as f:
                json.dump(config_data, f, indent=4)
            print(f"Updated 'current_project_step' in '{config_path}' to '{next_step_name}'.")
        except Exception as e:
            print(f"Error updating configuration file: {e}", file=sys.stderr)
            print("Please manually update 'current_project_step' if needed.", file=sys.stderr)
            return False # Failed to save state
        return True
    else:
        print(f"Failed to complete step '{next_step_name}'. 'current_project_step' in config remains '{current_project_step}'.", file=sys.stderr)
        return False
