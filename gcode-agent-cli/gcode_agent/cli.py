#!/usr/bin/env python3
import argparse
import os
import sys

# Import the client
from .core.gemini_client import GeminiClient
# Import command handlers
from .commands.init_command import handle_init
# Add imports for other commands later
from .commands.generate_command import handle_generate
from .commands.config_command import handle_config
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

    args = parser.parse_args()

    if not args.api_key:
        print("Error: Google AI API Key not found. "
              "Please set the GEMINI_API_KEY environment variable or use the --api-key argument.", file=sys.stderr)
        sys.exit(1)

    print(f"Welcome to gcode-agent! (Using model: {args.model})")
    print(f"Executing command: {args.command}")

    # --- Command Dispatch ---
    # Instantiate client here if needed by multiple commands, or within specific handlers
    gemini_client = None
    if args.command in ["generate"]: # Add other commands that need the client
        try:
            gemini_client = GeminiClient(
                api_key=args.api_key,
                model_name=args.model,
                verbose=args.verbose
            )
        except Exception as e:
            print(f"Error initializing Gemini Client: {e}", file=sys.stderr)
            sys.exit(1)

    if args.command == "init":
        # Call init command handler function (to be created)
        # print("Initializing project...")
        # Example: from .commands.init import handle_init; handle_init(args)
        # pass
        if not handle_init(args):
             sys.exit(1) # Exit if initialization failed

    elif args.command == "generate":
        # Call generate command handler function (to be created)
        # print(f"Generating step: {args.step or 'default/next'}")
        if gemini_client:
            # try:
            #     # TODO: Replace with actual prompt generation based on spec step
            #     spec_content = f"This is the content for step: {args.step or 'undefined'}. Please generate the required artifact."
            #     prompt = f"You are an AI assistant helping build a SaaS application. Based on the following specification step, generate the necessary code or configuration:\n\nSPECIFICATION:\n{spec_content}\n\nGENERATED OUTPUT:"

            #     response = gemini_client.generate_content(prompt)
            #     print("\n--- Generation Result ---")
            #     print(response)
            #     print("-------------------------")
            # except Exception as e:
            #     print(f"Error during generation: {e}", file=sys.stderr)
            #     sys.exit(1)
            if not handle_generate(args, gemini_client):
                 sys.exit(1) # Exit if generation failed
        else:
             print("Error: Gemini client failed to initialize.", file=sys.stderr)
             sys.exit(1)
    elif args.command == "config":
        # Call config command handler function (to be created)
        # print("Handling configuration...")
        # Example: from .commands.config import handle_config; handle_config(args)
        # pass
        if not handle_config(args):
             sys.exit(1)
    elif args.command == "serve-mcp":
        # Call MCP server start function (to be created)
        # print(f"Starting MCP server on {args.host}:{args.port}...")
        # Example: from .mcp import start_server; start_server(args)
        # pass
        try:
            start_server(host=args.host, port=args.port)
        except Exception as e:
            print(f"Failed to start MCP server: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        # Should not happen due to argparse 'required=True'
        print(f"Error: Unknown command '{args.command}'", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
