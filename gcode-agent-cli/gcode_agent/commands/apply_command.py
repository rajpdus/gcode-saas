import os
import shutil
import sys

AGENT_DIR = ".gcode-agent"
OUTPUT_SUBDIR = "outputs"

def handle_apply_to_workspace(args):
    """
    Handles copying a file from the agent's output directory to the workspace.
    """
    source_file_path = os.path.join(AGENT_DIR, OUTPUT_SUBDIR, args.file_path)

    if args.target_path:
        destination_file_path = args.target_path
    else:
        destination_file_path = args.file_path # Relative to CWD

    # Validation: Check if source_file_path exists and is a file
    if not os.path.isfile(source_file_path):
        print(f"Error: Source file not found or is not a file: {source_file_path}", file=sys.stderr)
        return

    # Create destination directory if it doesn't exist
    destination_dir = os.path.dirname(destination_file_path)
    if destination_dir: # Only create if dirname is not empty (e.g. for files in CWD)
        try:
            os.makedirs(destination_dir, exist_ok=True)
        except Exception as e:
            print(f"Error creating destination directory {destination_dir}: {e}", file=sys.stderr)
            return

    # Copy the file
    try:
        shutil.copy2(source_file_path, destination_file_path)
        print(f"Successfully copied '{source_file_path}' to '{destination_file_path}'")
    except Exception as e:
        print(f"Error copying file from '{source_file_path}' to '{destination_file_path}': {e}", file=sys.stderr)
        return
