#!/usr/bin/env python3
import argparse
import os
import sys

# Import the client
from .core.gemini_client import GeminiClient
# Import command handlers
from .commands.init_command import handle_init
from .commands.generate_command import handle_generate
from .commands.config_command import handle_config
from .commands.apply_command import handle_apply_to_workspace
from .commands.next_step_command import handle_next_step # New import
from .mcp_server import start_server # Import the server start function
# from .mcp import start_server

# Placeholder for Gemini models - we'll make this dynamic later
AVAILABLE_MODELS = [
    "gemini-2.5-pro-exp-03-25",
    "gemini-1.5-pro-latest",
    "gemini-1.5-flash-latest",
    "gemini-1.0-pro",
    # Add other relevant models as needed
]

def main():
    parser = argparse.ArgumentParser(
        description="gcode-agent: AI Agent CLI for generating SaaS applications using Gemini.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    # Global arguments
    parser.add_argument(
        "--model",
        help="The Gemini model to use for generation.",
        choices=AVAILABLE_MODELS,
        default=AVAILABLE_MODELS[0] # Changed default to the first element (new model)
    )
    parser.add_argument(
        "--api-key",
        help="Your Google AI API Key. Defaults to GEMINI_API_KEY environment variable.",
        default=os.environ.get("GEMINI_API_KEY")
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output."
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands", required=True)

    # --- 'init' command ---
    parser_init = subparsers.add_parser(
        "init",
        help="Initialize a new gcode-agent project in the current directory.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser_init.add_argument(
        "problem_description",
        help="High-level description of the problem the SaaS application will solve."
    )
    # Optional argument for template directory
    parser_init.add_argument(
        "--template-dir",
        help="Path to the directory containing the specification template files. If not provided, default templates will be used.",
        default="spec"
    )

    # --- 'generate' command ---
    parser_generate = subparsers.add_parser(
        "generate",
        help="Generate or update parts of the application based on the spec.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser_generate.add_argument(
        "step",
        nargs="?", # Optional: generate a specific step, otherwise maybe run full plan?
        help="Specify the generation step from the agent plan (e.g., 'step2', 'all')."
    )
    # Add generate-specific arguments here (e.g., --force, --dry-run)
    parser_generate.add_argument(
        "--apply",
        action="store_true",
        help="Attempt to automatically apply the generated plan (creates new files, flags modifications)."
    )

    # --- 'config' command ---
    parser_config = subparsers.add_parser(
        "config",
        help="View or modify gcode-agent configuration.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    # Add config-specific arguments (get/set specific keys)
    config_subparsers = parser_config.add_subparsers(dest="config_action", help="Configuration actions", required=True)

    # config list
    parser_config_list = config_subparsers.add_parser("list", help="List all configuration settings.")

    # config get <key>
    parser_config_get = config_subparsers.add_parser("get", help="Get the value of a specific configuration key.")
    parser_config_get.add_argument("key", help="The configuration key to retrieve.")

    # config set <key> <value>
    parser_config_set = config_subparsers.add_parser("set", help="Set the value of a specific configuration key.")
    parser_config_set.add_argument("key", help="The configuration key to set.")
    parser_config_set.add_argument("value", help="The value to set for the key.")

    # --- 'serve-mcp' command ---
    parser_mcp = subparsers.add_parser(
        "serve-mcp",
        help="Start the agent as an MCP server.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser_mcp.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host address to bind the MCP server to."
    )
    parser_mcp.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to run the MCP server on."
    )

    # --- 'apply-to-workspace' command ---
    parser_apply = subparsers.add_parser(
        "apply-to-workspace",
        help="Copy a file from the agent's output directory to the workspace.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser_apply.add_argument(
        "file_path",
        help="Path of the file within the '.gcode-agent/outputs/' directory to copy."
    )
    parser_apply.add_argument(
        "--target-path",
        help="Optional. Path in the workspace to copy the file to. Defaults to the same relative path in the CWD."
    )
    parser_apply.set_defaults(func=handle_apply_to_workspace)

    # --- 'next' command ---
    parser_next = subparsers.add_parser(
        "next",
        help="Executes the next step in the project generation sequence based on config."
    )
    parser_next.add_argument(
        "--apply",
        action="store_true",
        help="Attempt to automatically apply the plan generated for the next step."
    )
    # --verbose is global, so next_parser will inherit it.
    # --model is global, so next_parser will inherit it. handle_next_step can choose to use it or config.
    parser_next.set_defaults(func=handle_next_step)


    args = parser.parse_args()

    # Commands that require API key and Gemini Client
    commands_requiring_client = ["generate", "init", "next"]

    # API key check for relevant commands
    if args.command in commands_requiring_client and not args.api_key:
        print(f"Error: Google AI API Key not found for command '{args.command}'. "
              "Please set the GEMINI_API_KEY environment variable or use the --api-key argument.", file=sys.stderr)
        sys.exit(1)
    elif args.command == "config" and args.config_action == "set" and not args.api_key: # config set still needs key
        print("Error: Google AI API Key not found for 'config set'. "
              "Please set the GEMINI_API_KEY environment variable or use the --api-key argument.", file=sys.stderr)
        sys.exit(1)

    print(f"Welcome to gcode-agent! (Using model: {args.model if hasattr(args, 'model') and args.model else 'N/A'})")
    print(f"Executing command: {args.command}")

    # --- Client Initialization & Command Dispatch ---
    gemini_client = None
    if args.command in commands_requiring_client:
        try:
            gemini_client = GeminiClient(
                api_key=args.api_key,
                model_name=args.model,
                verbose=args.verbose
            )
        except Exception as e:
            print(f"Error initializing Gemini Client: {e}", file=sys.stderr)
            sys.exit(1)

    # Dispatch to the appropriate handler function
    # For commands requiring the client, pass it. Otherwise, just pass args.
    if hasattr(args, 'func'):
        exit_code = 0
        try:
            if args.command in commands_requiring_client:
                if not args.func(args, gemini_client): # Assumes handler returns True for success, False for failure
                    exit_code = 1
            else:
                # For commands like 'config' (except set which is handled by API key check) or 'apply-to-workspace'
                # Some config actions might return False on failure, so capture that.
                if hasattr(args, 'config_action') and args.config_action in ["get", "set"]: # list always returns True currently
                     if not args.func(args):
                         exit_code = 1
                else: # For apply-to-workspace or config list
                    args.func(args) # These don't currently return success/failure bools in a way that's used here
            
            if exit_code != 0:
                 sys.exit(exit_code)

        except Exception as e:
            print(f"An error occurred executing command '{args.command}': {e}", file=sys.stderr)
            sys.exit(1)
    else:
        # Fallback for commands not using set_defaults, though all should.
        print(f"Error: No handler function defined for command '{args.command}'", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
