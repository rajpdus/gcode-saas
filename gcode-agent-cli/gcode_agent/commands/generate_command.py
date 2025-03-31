import os
import sys
import json
import glob # To find previous outputs
from typing import Optional

# Import the plan parser
from .core.plan_parser import parse_plan, FileModification

# Import the tool API (assuming it's available like this)
# We need to know how to actually call the tools.
# Let's assume there's an 'api' object available somehow or passed in.
# For now, we'll define a placeholder function.
def call_edit_file_tool(target_file: str, code_edit: str, instructions: str):
    """Placeholder for the actual tool call."""
    # In reality, this would invoke the available API:
    # return default_api.edit_file(
    #     target_file=target_file,
    #     code_edit=code_edit,
    #     instructions=instructions
    # )
    print(f"[SIMULATED TOOL CALL] edit_file")
    print(f"  target_file: {target_file}")
    print(f"  instructions: {instructions}")
    print(f"  code_edit:\n---\n{code_edit}\n---")
    # Simulate success for now
    return {"status": "success"} # Or whatever the tool returns

# Constants (consider moving to a shared config module later)
AGENT_DIR = ".gcode-agent"
SPEC_SUBDIR = "spec"
OUTPUT_SUBDIR = "outputs"
CONFIG_FILE = "config.json"

# Mapping from step argument to TEMPLATE filename
STEP_TEMPLATE_MAP = {
    "step1": "step1-problem-definition.md",
    "step2": "step2-ia-entities.md",
    "step3": "step3-dynamodb-model.md",
    "step4": "step4-generate-ui.md",
    "step5": "step5-integrate-backend-auth.md",
    "step6": "step6-prepare-deployment.md",
    "agent-plan": "agent-plan.md" # Include the main plan if needed
}

def get_step_number(step_arg: str) -> Optional[int]:
    """Extracts the number from a step argument like 'step3'."""
    if step_arg.startswith('step') and step_arg[4:].isdigit():
        return int(step_arg[4:])
    return None

def handle_generate(args, client):
    """Handles the generation of application parts based on spec steps."""
    step_arg = args.step
    verbose = args.verbose

    # 1. Check if initialized and directories exist
    if not os.path.isdir(AGENT_DIR):
        print(f"Error: Project not initialized. Run 'gcode-agent init <spec_dir>' first.", file=sys.stderr)
        return False
    target_spec_dir = os.path.join(AGENT_DIR, SPEC_SUBDIR)
    target_output_dir = os.path.join(AGENT_DIR, OUTPUT_SUBDIR)
    if not os.path.isdir(target_spec_dir) or not os.path.isdir(target_output_dir):
        print(f"Error: Internal directories ('{SPEC_SUBDIR}' or '{OUTPUT_SUBDIR}') not found.", file=sys.stderr)
        print(f"Please try running 'init' again.")
        return False

    # 2. Determine Step Template and Number
    if not step_arg:
        # TODO: Implement logic to determine the next step from config or state
        print("Error: Step argument (e.g., 'step1', 'step2') is required for now.", file=sys.stderr)
        return False

    if step_arg not in STEP_TEMPLATE_MAP:
        print(f"Error: Unknown step '{step_arg}'. Available steps: {list(STEP_TEMPLATE_MAP.keys())}", file=sys.stderr)
        return False

    current_step_num = get_step_number(step_arg)
    spec_template_filename = STEP_TEMPLATE_MAP[step_arg]
    spec_template_filepath = os.path.join(target_spec_dir, spec_template_filename)

    if not os.path.isfile(spec_template_filepath):
        print(f"Error: Specification template not found for step '{step_arg}': {spec_template_filepath}", file=sys.stderr)
        return False

    # 3. Read Spec Template for Current Step
    try:
        if verbose:
            print(f"Reading specification template: {spec_template_filepath}")
        with open(spec_template_filepath, 'r') as f:
            current_spec_template_content = f.read()
    except IOError as e:
        print(f"Error reading specification template '{spec_template_filepath}': {e}", file=sys.stderr)
        return False

    # 4. Read Outputs from Previous Steps
    previous_steps_context = ""
    if current_step_num and current_step_num > 1:
        if verbose:
            print(f"Reading outputs from previous steps (1 to {current_step_num - 1})...")
        context_parts = []
        for i in range(1, current_step_num):
            prev_step_output_file = os.path.join(target_output_dir, f"step{i}_output.md")
            if os.path.isfile(prev_step_output_file):
                try:
                    with open(prev_step_output_file, 'r') as f:
                        content = f.read()
                        context_parts.append(f"--- START CONTEXT FROM STEP {i} ---\n{content}\n--- END CONTEXT FROM STEP {i} ---\n")
                        if verbose:
                             print(f"  Loaded context from: {prev_step_output_file}")
                except IOError as e:
                    print(f"Warning: Could not read previous output file '{prev_step_output_file}': {e}", file=sys.stderr)
            elif verbose:
                 print(f"  No output file found for step {i} at: {prev_step_output_file}")
        previous_steps_context = "\n".join(context_parts)

    # 5. Construct Prompt with Context
    prompt_context = previous_steps_context
    prompt = (
        f"You are an AI coding agent ({args.model}) following a multi-step plan to build a SaaS application."
        f"You have already completed Steps 1 through {current_step_num - 1 if current_step_num else 0}. The context from those steps is provided below.\n\n"
        f"{prompt_context}\n"
        f"Your current task is to execute Step '{step_arg}'. The template/guidelines for this step are:\n\n"
        f"--- TEMPLATE/GUIDELINES (Step: {step_arg}) ---\n"
        f"{current_spec_template_content}\n"
        f"--- END TEMPLATE/GUIDELINES ---\n\n"
        f"Based on the previous context AND the template for Step '{step_arg}', generate the plan for file modifications required for this step."
        f"Describe the actions (create/modify file) and include the full intended content for each file in Markdown code blocks."
        f"Generate the plan for Step '{step_arg}':"
    )

    # 6. Call Gemini Client
    if not client:
         print("Error: Gemini client was not provided or failed to initialize.", file=sys.stderr)
         return False

    plan_text = ""
    try:
        if verbose:
            print(f"Sending prompt for step '{step_arg}' plan (with context) to Gemini...")
        plan_text = client.generate_content(prompt)
        print(f"\n--- Generated Plan for Step: {step_arg} ---")
        print(plan_text)
        print(f"-----------------------------------------")

    except Exception as e:
        print(f"Error during plan generation for step '{step_arg}': {e}", file=sys.stderr)
        return False

    # 7. Save the generated plan as output for this step
    step_output_filename = os.path.join(target_output_dir, f"{step_arg}_output.md")
    try:
        if verbose:
            print(f"Saving generated plan to: {step_output_filename}")
        with open(step_output_filename, 'w') as f:
            f.write(plan_text)
    except IOError as e:
        print(f"Warning: Failed to save step output to '{step_output_filename}': {e}", file=sys.stderr)
        # Continue even if saving fails, but warn user

    # 8. Parse the Plan
    if verbose:
        print("Parsing generated plan...")
    modifications = parse_plan(plan_text)

    if not modifications:
        print("Could not extract any file modifications from the plan. No files created/modified.")
        return True # Consider step done if plan generated, even if no actions parse

    # 9. Execute the Plan (Apply Changes using Tools)
    print(f"\n--- Applying Plan --- ({'Auto-apply ENABLED' if args.apply else 'Auto-apply DISABLED (use --apply)'})")
    execution_success = True
    applied_files = []
    needs_manual_review = []

    # Use the --apply flag passed in args
    auto_apply = args.apply

    for mod in modifications:
        target_file_path = os.path.join(".", mod.relative_path) # Write to current dir

        if not os.path.exists(target_file_path):
            if auto_apply:
                print(f"Attempting to CREATE file: '{mod.relative_path}'")
                try:
                    # --- Actual Tool Call (using placeholder) ---
                    instructions = f"Create the new file '{mod.relative_path}' as specified in the plan for step {step_arg}. Ensure correct indentation and structure."
                    # For creating a new file, the code_edit is just the full content.
                    result = call_edit_file_tool(
                        target_file=target_file_path,
                        code_edit=mod.content,
                        instructions=instructions
                    )
                    # TODO: Check result for actual success/failure from tool
                    print(f"Successfully applied creation for: {mod.relative_path}")
                    applied_files.append(mod.relative_path + " (Created)")
                except Exception as tool_error:
                    print(f"Error applying tool to create {mod.relative_path}: {tool_error}", file=sys.stderr)
                    execution_success = False
                    needs_manual_review.append(mod.relative_path + " (Tool Error)")
            else:
                print(f"[ACTION REQUIRED] Plan suggests CREATING file: '{mod.relative_path}'")
                print(f"  Run with '--apply' flag to attempt automatic creation.")
                print(f"  Content to write:\n---\n{mod.content}\n---")
                needs_manual_review.append(mod.relative_path + " (New File - Manual Apply)")
        else:
            # File exists - requires manual review for modification
            print(f"[ACTION REQUIRED] Plan suggests MODIFYING existing file: '{mod.relative_path}'")
            print(f"  Automatic modification is not supported. Please review the suggested content below and apply changes manually.")
            print(f"  Suggested Content:\n---\n{mod.content}\n---")
            needs_manual_review.append(mod.relative_path + " (Existing File - Manual Apply)")

    # 10. Report Results
    print("\n--- Plan Execution Summary ---")
    if applied_files:
        print("Files automatically created/modified (or simulated):")
        for f in applied_files:
            print(f"  - {f}")
    if needs_manual_review:
        print("Files requiring manual review/action:")
        for f in needs_manual_review:
            print(f"  - {f}")

    if not execution_success:
        print("\nWarning: One or more errors occurred during plan execution.")
    elif not needs_manual_review and applied_files:
        print("\nPlan applied successfully.")
    elif not needs_manual_review and not applied_files and not auto_apply:
         print("\nPlan generated, but no files were created (requires manual application or '--apply' flag)." )
    else:
        print("\nPlan generation complete. Please perform manual review steps.")

    # TODO: Update the config file with the completed step only if execution_success is True
    return execution_success # Return overall success of execution attempt
