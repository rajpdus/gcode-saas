import os
import sys
import argparse # For potentially reusing args parsing logic
from mcp.server.fastmcp import FastMCP
from mcp import types as mcp_types

# Import handlers from our CLI commands
from .commands.init_command import handle_init
from .commands.generate_command import handle_generate, AGENT_DIR as GCODE_AGENT_DIR, SPEC_SUBDIR
from .commands.config_command import handle_config, read_config, ALLOWED_CONFIG_KEYS

# Import Gemini client (needed for generate)
from .core.gemini_client import GeminiClient

# Create the FastMCP instance
mcp_app = FastMCP(
    name="gcode-agent",
    version="0.1.0",
    description="MCP server for the gcode-agent CLI tool."
)

# --- Helper to Get Gemini Client ---
# MCP tools might need the client, so we need a way to initialize it.
# This assumes API key comes from environment for the server process.
def get_gemini_client(model: str = None) -> GeminiClient:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set.")

    # Determine model: Use provided, or read from config, or default
    if not model:
        config = read_config()
        if config and config.get("model"):
            model = config.get("model")
        else:
            # Fallback to a default model
            model = "gemini-2.5-pro-exp-03-25"

    try:
        # verbose=True can be noisy in server logs, maybe make configurable?
        return GeminiClient(api_key=api_key, model_name=model, verbose=False)
    except Exception as e:
        print(f"Error initializing Gemini Client for MCP: {e}", file=sys.stderr)
        # Re-raise or handle appropriately for MCP context
        raise RuntimeError(f"Failed to initialize Gemini Client: {e}")

# --- MCP Resources --- (Exposing Spec Files)
@mcp_app.resource(f"spec://{{filename}}")
def get_spec_resource(filename: str) -> str:
    """Provides access to specification files within the initialized project."""
    spec_dir = os.path.join(GCODE_AGENT_DIR, SPEC_SUBDIR)
    if not os.path.isdir(spec_dir):
        raise ValueError(f"Project not initialized or spec dir not found ('{spec_dir}')")

    # Basic path safety
    if ".." in filename or filename.startswith("/"):
        raise ValueError("Invalid filename requested.")

    file_path = os.path.join(spec_dir, filename)
    if not os.path.isfile(file_path):
        raise ValueError(f"Spec file '{filename}' not found.")

    try:
        with open(file_path, 'r') as f:
            return f.read()
    except IOError as e:
        raise ValueError(f"Error reading spec file '{filename}': {e}")

# --- MCP Tools --- (Exposing Agent Commands)

@mcp_app.tool()
def initialize_project(spec_dir: str) -> str:
    """Initializes a new gcode-agent project using the provided spec directory."""
    # Simulate argparse namespace for the handler
    # Need to handle the model argument potentially. Let's assume default for now.
    args = argparse.Namespace(
        spec_dir=spec_dir,
        verbose=False, # Or get from server config?
        model=None # `handle_init` reads model from args, might need adjustment
    )
    config = read_config() # Read existing config
    args.model = config.get("model", "gemini-2.5-pro-exp-03-25") if config else "gemini-2.5-pro-exp-03-25"

    if handle_init(args):
        return f"Project initialized successfully in '{GCODE_AGENT_DIR}'."
    else:
        # Errors should ideally be raised by handle_init or handled here
        # For now, return a generic failure message
        return "Error: Project initialization failed. Check server logs."

@mcp_app.tool()
def generate_step(step: str, model: str = None) -> str:
    """Generates the plan for a specific step based on the initialized spec."""
    client = get_gemini_client(model=model) # Get client with specified or default model
    # Simulate argparse namespace
    args = argparse.Namespace(
        step=step,
        verbose=False, # Server logs are separate
        model=client.model_name # Use the actual model resolved by get_gemini_client
    )

    # We need to capture the output of handle_generate instead of printing it
    # Refactoring handle_generate to return the plan string might be better.
    # For now, we try to capture stdout (this is fragile).
    from io import StringIO
    import sys
    old_stdout = sys.stdout
    redirected_output = StringIO()
    sys.stdout = redirected_output

    success = False
    try:
        # Need to pass the initialized client to the handler
        success = handle_generate(args, client)
    finally:
        sys.stdout = old_stdout # Restore stdout

    output_str = redirected_output.getvalue()

    if success:
        # Extract the plan part from the captured output (crude)
        plan_marker = f"--- Generated Plan for Step: {step} ---"
        if plan_marker in output_str:
            plan_content = output_str.split(plan_marker, 1)[1]
            plan_content = plan_content.split("-----------------------------------------", 1)[0]
            # Add info about manual application
            plan_content += "\n\nINFO: Plan generated. Manual application required via CLI or IDE."
            return plan_content.strip()
        else:
            return "Generation seemed successful, but could not extract plan from output."
    else:
        # Try to return error messages from output if possible
        if output_str:
             return f"Error during generation: {output_str.strip()}"
        else:
             return f"Error: Step '{step}' generation failed. Check server logs."

@mcp_app.tool()
def get_config_value(key: str) -> str:
    """Gets a specific configuration value."""
    config = read_config()
    if not config:
        return "Error: Configuration not found."
    if key in config:
        # Convert non-string values for display
        return json.dumps(config[key])
    else:
        return f"Error: Key '{key}' not found."

@mcp_app.tool()
def set_config_value(key: str, value: str) -> str:
    """Sets a specific configuration value (Allowed: model, current_step)."""
    if key not in ALLOWED_CONFIG_KEYS:
        return f"Error: Setting key '{key}' is not allowed. Allowed: {ALLOWED_CONFIG_KEYS}"

    # Simulate argparse for the handler
    args = argparse.Namespace(
        config_action="set",
        key=key,
        value=value
    )
    if handle_config(args):
        return f"Successfully set '{key}'."
    else:
        return f"Error setting '{key}'. Check server logs."

# Function to start the server (called by cli.py)
def start_server(host: str, port: int):
    """Runs the MCP server using Uvicorn."""
    print(f"Starting gcode-agent MCP server on http://{host}:{port}")
    print(f"Using config dir: {GCODE_AGENT_DIR}")
    print(f"Allowed config keys to set: {ALLOWED_CONFIG_KEYS}")
    # Make sure API key is available
    if not os.environ.get("GEMINI_API_KEY"):
        print("Warning: GEMINI_API_KEY environment variable not set. Gemini calls will fail.", file=sys.stderr)

    # `mcp_app.run()` is a convenience wrapper around uvicorn
    # It doesn't directly take host/port in the same way as uvicorn.run
    # We need to use uvicorn directly here.
    import uvicorn
    uvicorn.run(mcp_app.app, host=host, port=port, log_level="info")
