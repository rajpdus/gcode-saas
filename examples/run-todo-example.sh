#!/bin/bash

# Script to automate generating the ToDo application using gcode-agent
# Assumes:
# - You are running this script from the gcode-agent-cli directory.
# - Specification templates are in the ./spec/ directory.
# - GEMINI_API_KEY environment variable is set.
# - ./gcode_agent.py is executable.

set -e # Exit immediately if a command exits with a non-zero status.

# --- Configuration ---
SPEC_DIR="./spec" # Location of the spec templates
OUTPUT_DIR="./my-todo-app-generated" # Where the ToDo app code will be generated
AGENT_SCRIPT="./gcode_agent.py"
MODEL="gemini-2.5-pro-exp-03-25" # Model to use for generation

# --- Check Prerequisites ---
if [ ! -d "$SPEC_DIR" ]; then
  echo "Error: Specification template directory not found: $SPEC_DIR" >&2
  echo "Please ensure the spec templates are in the correct location." >&2
  exit 1
fi

if [ ! -f "$AGENT_SCRIPT" ]; then
  echo "Error: Agent script not found: $AGENT_SCRIPT" >&2
  exit 1
fi

if [ -z "$GEMINI_API_KEY" ]; then
  echo "Error: GEMINI_API_KEY environment variable is not set." >&2
  exit 1
fi

# --- Setup Output Directory ---
echo "Creating output directory: $OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR"

# --- Run Generation Steps --- 
echo "\nChanging directory to: $OUTPUT_DIR"
cd "$OUTPUT_DIR"

AGENT_SCRIPT_REL="../gcode_agent.py" # Relative path from output dir
SPEC_DIR_REL="../spec"              # Relative path from output dir

# 1. Initialize Project
echo "\nSTEP 0: Initializing project in $(pwd)..."
"$AGENT_SCRIPT_REL" init "$SPEC_DIR_REL" --model "$MODEL"

# 2. Generate Step 1 (Definition - usually no code generated)
echo "\nSTEP 1: Generating definition step..."
"$AGENT_SCRIPT_REL" generate step1 --model "$MODEL"

# 3. Generate Step 2 (Entities/IA - usually no code generated)
echo "\nSTEP 2: Generating entities/IA step..."
"$AGENT_SCRIPT_REL" generate step2 --model "$MODEL"

# 4. Generate Step 3 (Data Model - apply changes)
echo "\nSTEP 3: Generating data model step (with --apply)..."
"$AGENT_SCRIPT_REL" generate step3 --apply --model "$MODEL"

# 5. Generate Step 4 (UI - apply changes)
echo "\nSTEP 4: Generating UI step (with --apply)..."
"$AGENT_SCRIPT_REL" generate step4 --apply --model "$MODEL"

# 6. Generate Step 5 (Backend - apply changes)
echo "\nSTEP 5: Generating backend step (with --apply)..."
"$AGENT_SCRIPT_REL" generate step5 --apply --model "$MODEL"

# 7. Generate Step 6 (Deployment - apply changes)
echo "\nSTEP 6: Generating deployment step (with --apply)..."
"$AGENT_SCRIPT_REL" generate step6 --apply --model "$MODEL"

# --- Completion Message ---
echo "\n--------------------------------------------------"
echo "ToDo Application Generation Process Complete!"
echo "--------------------------------------------------"
echo "Generated code is in: $(pwd)"
echo ""
echo "Next Steps:"
echo "1. Review the generated files."
echo "2. Manually merge any changes flagged for existing files during generation."
echo "3. Install backend dependencies: cd backend && pip install -r requirements.txt"
echo "4. Install frontend dependencies: cd ../frontend && npm install"
echo "5. Run linters/formatters and perform necessary debugging."
echo "6. Configure and test deployment scripts."
echo "--------------------------------------------------"

# Optional: Go back to the original directory
# cd .. 