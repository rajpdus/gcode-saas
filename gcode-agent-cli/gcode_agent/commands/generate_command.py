import os
import sys
import json
import glob # To find previous outputs
from typing import Optional, List, Dict

# Import the Gemini client
from ..core.gemini_client import GeminiClient

# Import the tool API placeholder
def call_edit_file_tool(target_file: str, code_edit: str, instructions: str):
    """Actually create or modify the file."""
    print(f"[EDIT_FILE TOOL] {instructions}")
    print(f"  target_file: {target_file}")
    
    # Create directory structure if needed
    target_dir = os.path.dirname(target_file)
    if target_dir and not os.path.exists(target_dir):
        try:
            os.makedirs(target_dir, exist_ok=True)
            print(f"  Created directory: {target_dir}")
        except Exception as e:
            print(f"  Error creating directory {target_dir}: {e}", file=sys.stderr)
            return {"status": "error", "message": f"Failed to create directory: {str(e)}"}
    
    # Write the file content
    try:
        with open(target_file, 'w') as f:
            f.write(code_edit)
        print(f"  Successfully wrote file: {target_file}")
        return {"status": "success"}
    except Exception as e:
        print(f"  Error writing file {target_file}: {e}", file=sys.stderr)
        return {"status": "error", "message": f"Failed to write file: {str(e)}"}

# Constants
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
    "agent-plan": "agent-plan.md"
}

def get_step_number(step_arg: str) -> Optional[int]:
    """Extracts the number from a step argument like 'step3'."""
    if step_arg.startswith('step') and step_arg[4:].isdigit():
        return int(step_arg[4:])
    return None

def get_file_type(file_path):
    """Determines if a file is code or documentation based on its extension"""
    code_extensions = ['.js', '.jsx', '.ts', '.tsx', '.py', '.c', '.cpp', '.java', '.go', '.rs', '.php', '.rb']
    doc_extensions = ['.md', '.txt', '.rst', '.adoc']
    
    _, extension = os.path.splitext(file_path)
    
    if extension in code_extensions:
        return "code"
    elif extension in doc_extensions:
        return "documentation"
    else:
        # For unknown extensions, determine based on path
        if 'doc' in file_path.lower() or 'readme' in file_path.lower():
            return "documentation"
        return "code"  # Default to code

def parse_plan_with_llm(client: GeminiClient, plan_text: str, verbose: bool = False) -> List[Dict]:
    """
    Uses the LLM itself to parse the generated plan text and extract file modifications
    into a structured JSON format.

    Args:
        client: The initialized GeminiClient.
        plan_text: The plan text generated by the first LLM call.
        verbose: Whether to print verbose output.

    Returns:
        A list of dictionaries, where each dictionary represents a file modification
        with keys 'action', 'path', and 'content'. Returns empty list on failure.
    """
    parsing_prompt = f"""
Analyze the following plan text generated by an AI agent. Extract all file creation or modification instructions.
Output *only* a valid JSON list where each object represents one file action and has the following keys:
- "action": A string, either "create" or "modify".
- "path": A string, the relative file path (e.g., "src/app.py").
- "content": A string containing the full intended content of the file. For large or complex files, the content may be placeholder or skeleton code.
- "is_complete": A boolean, true if the content represents a complete implementation, false for placeholder/skeleton code that needs further expansion.
- "priority": An integer from 1-3, where 1 is highest priority (essential structure files), 2 is medium (component files), 3 is lowest (optional/enhancement files).
- "file_type": A string, either "code" or "documentation".

Do not include any explanations, introductory text, or markdown formatting outside the JSON structure itself.
Ensure the JSON is well-formed.

Plan Text to Parse:
```
{plan_text}
```

JSON Output:
"""

    if verbose:
        print("\n--- Sending Plan to LLM for Parsing ---")
        # print(parsing_prompt) # Can be very long, omit for brevity unless debugging

    try:
        response_text = client.generate_content(parsing_prompt)
        
        if verbose:
            print("--- Received Parsing Result from LLM ---")
            print(response_text)
            print("---------------------------------------")

        # Clean potential markdown fences around the JSON
        cleaned_response = response_text.strip().strip('```json').strip('```').strip()
        
        # Parse the JSON response
        modifications = json.loads(cleaned_response)
        
        # Basic validation of the parsed structure
        if not isinstance(modifications, list):
            print(f"Warning: LLM parser did not return a JSON list. Received: {type(modifications)}", file=sys.stderr)
            return []
            
        valid_modifications = []
        for item in modifications:
            if isinstance(item, dict) and \
               all(key in item for key in ['action', 'path', 'content']) and \
               isinstance(item['action'], str) and \
               isinstance(item['path'], str) and \
               isinstance(item['content'], str) and \
               item['action'] in ['create', 'modify']:
                valid_modifications.append(item)
            else:
                print(f"Warning: Skipping invalid item in parsed JSON: {item}", file=sys.stderr)
               
        return valid_modifications

    except json.JSONDecodeError as e:
        print(f"Error: Failed to decode JSON response from LLM parser: {e}", file=sys.stderr)
        print(f"Raw response was:\n{response_text}")
        return []
    except Exception as e:
        print(f"Error during LLM plan parsing: {e}", file=sys.stderr)
        return []

def handle_generate(args, client):
    """Handles the generation of application parts based on spec steps."""
    step_arg = args.step
    verbose = args.verbose

    # 1. Check if initialized and directories exist
    if not os.path.isdir(AGENT_DIR):
        print(f"Error: Project not initialized. Run 'gcode-agent init <problem_description>' first.", file=sys.stderr)
        return False
    target_spec_dir = os.path.join(AGENT_DIR, SPEC_SUBDIR)
    target_output_dir = os.path.join(AGENT_DIR, OUTPUT_SUBDIR)
    if not os.path.isdir(target_spec_dir) or not os.path.isdir(target_output_dir):
        print(f"Error: Internal directories ('{SPEC_SUBDIR}' or '{OUTPUT_SUBDIR}') not found.", file=sys.stderr)
        print(f"Please try running 'init' again.")
        return False

    # 2. Determine Step Template and Number
    if not step_arg:
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
    
    # Define step_output_filename here, before it's used
    step_output_filename = os.path.join(target_output_dir, f"{step_arg}_output.md")
    
    # Read problem description from config if possible
    problem_description = ""
    config_path = os.path.join(AGENT_DIR, CONFIG_FILE)
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                config_data = json.load(f)
                problem_description = config_data.get("problem_description", "")
        except Exception as e:
            if verbose:
                print(f"Warning: Could not read problem description from config: {e}", file=sys.stderr)
    
    # Determine if we are dealing with code or documentation
    is_code_step = any(pattern in step_arg.lower() for pattern in ["generate", "implement", "create", "code", "ui"])
    is_initial_plan = not os.path.exists(step_output_filename)
    
    # Add instruction for incremental generation for code steps
    incremental_instruction = """
IMPORTANT INSTRUCTIONS FOR CODE GENERATION:
1. DO NOT generate complete implementations for all files in one plan. 
2. For documentation files (.md, .txt), full content is acceptable.
3. For code files:
   - Provide directory structure and file organization first
   - For each code file:
     - Include necessary imports, key function signatures, and types/interfaces
     - Omit implementation details for large functions
     - Add comments indicating what parts need further implementation
     - Keep React components to import statements and basic function structure
   - Mark files as incomplete using is_complete:false in your response

4. Focus on code organization, architecture design, and core interfaces.

GENERATING PLANS IN PHASES:
1. Initial Phase: Generate directory structure, essential configuration files, and code skeletons
2. Intermediate Phase: Focus on essential functionality and interfaces
3. Final Phase: Add implementation details once structure is reviewed

This plan should only focus on the first phase. We'll handle implementation details incrementally in follow-up plans.
""" if is_code_step and is_initial_plan else ""
    
    # Add instructions for parsing the JSON if this is not the initial plan
    parsing_instruction = """
PLAN PARSING INSTRUCTIONS:
When generating JSON from this plan, please ensure each file action includes these properties:
- file_type: 'code' or 'documentation'
- is_complete: whether the file content represents complete implementation
- priority: 1 (essential), 2 (important), 3 (optional)
""" if not is_initial_plan else ""
    
    prompt = (
        f"You are an AI coding agent ({args.model}) following a multi-step plan to build a SaaS application that solves "
        f"the following problem: \"{problem_description}\"\n\n"
        f"You have already completed Steps 1 through {current_step_num - 1 if current_step_num else 0}. The context from those steps is provided below.\n\n"
        f"{prompt_context}\n"
        f"Your current task is to execute Step '{step_arg}'. The template/guidelines for this step are:\n\n"
        f"--- TEMPLATE/GUIDELINES (Step: {step_arg}) ---\n"
        f"{current_spec_template_content}\n"
        f"--- END TEMPLATE/GUIDELINES ---\n\n"
        f"{incremental_instruction}\n\n"
        f"Based on the problem description, previous context, AND the template for Step '{step_arg}', generate the plan for file modifications required for this step. "
        f"Make sure your plan is directly relevant to the specific problem being solved.\n\n"
        f"Describe the actions (create/modify file) and include the intended content for each file in Markdown code blocks."
        f"Use a clear structure, for example:\n* Action: create | modify\n* File Path: relative/path/to/file.ext\n* Content:\n  ```language\n  file content here\n  ```\n"
        f"{parsing_instruction}\n\n"
        f"Generate the plan for Step '{step_arg}':"
    )

    # 6. Call Gemini Client to Generate the Plan
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
    try:
        if verbose:
            print(f"Saving generated plan to: {step_output_filename}")
        with open(step_output_filename, 'w') as f:
            f.write(plan_text)
    except IOError as e:
        print(f"Warning: Failed to save step output to '{step_output_filename}': {e}", file=sys.stderr)
        # Continue even if saving fails, but warn user

    # 8. Parse the Plan using LLM
    if verbose:
        print("Parsing generated plan using LLM...")
    
    # Call the new parsing function
    modifications = parse_plan_with_llm(client, plan_text, verbose)

    if not modifications:
        print("Could not extract any file modifications from the plan (LLM Parsing). No files created/modified.")
        return True # Consider step done if plan generated, even if no actions parse

    # 9. Execute the Plan (Apply Changes using Tools)
    print(f"\n--- Applying Plan --- ({'Auto-apply ENABLED' if args.apply else 'Auto-apply DISABLED (use --apply)'})")
    execution_success = True
    applied_files = []
    needs_manual_review = []

    auto_apply = args.apply

    # Sort modifications by priority, file type and completeness
    # Docs first, then essential code structure, then components
    sorted_modifications = sorted(modifications, key=lambda m: (
        # Documentation always first
        0 if m.get('file_type', '') == 'documentation' else 1,
        # Then by priority (1 is highest)
        int(m.get('priority', 2)),
        # Complete implementations before incomplete ones
        0 if m.get('is_complete', True) else 1
    ))
    
    # For code files with a lot of content, provide a warning and note for incremental development
    for mod in sorted_modifications:
        # Extract info from the parsed dictionary
        action = mod.get('action', '').lower()
        relative_path = mod.get('path', '')
        content = mod.get('content', '')
        file_type = mod.get('file_type', get_file_type(relative_path))
        is_complete = mod.get('is_complete', True)
        
        # For large code files, provide a note
        if file_type == "code" and len(content) > 500 and not is_complete:
            print(f"\nNote: File '{relative_path}' contains a large amount of code. Consider implementing it incrementally.")
        
        if not relative_path: # Skip if path is missing
            print("Warning: Skipping modification with missing path.")
            continue
        if ".." in relative_path or relative_path.startswith("/"):
            print(f"Warning: Skipping potentially invalid path found in parsed plan: {relative_path}")
            continue
        
        # Create files in the outputs directory instead of current directory
        target_file_path = os.path.join(target_output_dir, relative_path)

        # For code files with excessive content but not marked as complete, truncate and add a note
        if file_type == "code" and len(content) > 1000 and not is_complete:
            # Truncate the content but preserve structure - keep headers and function signatures
            # This is a simple approach - in a production system, you might want to use 
            # an AST parser to intelligently truncate code
            lines = content.split("\n")
            if len(lines) > 50:  # If more than 50 lines
                # Keep first 20 lines to preserve imports and structure
                header_lines = lines[:20]
                # Keep last 10 lines to preserve closing braces/structure
                footer_lines = lines[-10:]
                # Generate a note for the middle
                note_lines = [
                    "", 
                    "// ... Content truncated for incremental implementation ...",
                    "// This is a skeleton/placeholder. Implement incrementally after reviewing structure.",
                    ""
                ]
                # Combine to form truncated content
                content = "\n".join(header_lines + note_lines + footer_lines)
                
        if action == "create":
            if not os.path.exists(target_file_path):
                if auto_apply:
                    print(f"Attempting to CREATE file: '{relative_path}' in outputs directory")
                    try:
                        instructions = f"Create the new file '{relative_path}' in outputs directory as specified in the plan for step {step_arg}."
                        result = call_edit_file_tool(
                            target_file=target_file_path,
                            code_edit=content, # Use the full content for creation
                            instructions=instructions
                        )
                        # Check result for success/failure
                        if result.get("status") == "success":
                            print(f"Successfully applied creation for: {relative_path}")
                            status_note = " (Created in outputs directory - Skeleton/Placeholder)" if not is_complete else " (Created in outputs directory)"
                            applied_files.append(relative_path + status_note)
                        else:
                            print(f"Error creating file: {result.get('message', 'Unknown error')}")
                            execution_success = False
                            needs_manual_review.append(relative_path + f" (Creation Failed - {result.get('message', 'Unknown error')})")
                    except Exception as tool_error:
                        print(f"Error applying tool to create {relative_path}: {tool_error}", file=sys.stderr)
                        execution_success = False
                        needs_manual_review.append(relative_path + " (Tool Error - Create)")
                else:
                    # Create action, but --apply not used
                    status_note = " - skeleton/placeholder" if not is_complete else ""
                    needs_manual_review.append(relative_path + f" (Needs Creation in outputs{status_note} - content in {step_output_filename})")
            else:
                 # File already exists, treat as modification for manual review
                 print(f"File '{relative_path}' already exists in outputs directory. Planned action was 'create'. Flagging for manual review.")
                 needs_manual_review.append(relative_path + f" (Needs Manual Merge - Exists in outputs, planned create - details in {step_output_filename})")

        elif action == "modify":
             if os.path.exists(target_file_path):
                 # Always flag modifications for manual review for now
                 status_note = " - partial update" if not is_complete else ""
                 needs_manual_review.append(relative_path + f" (Needs Manual Modification in outputs{status_note} - details in {step_output_filename})")
             else:
                  # Planned modification, but file doesn't exist. Flag for review.
                  print(f"File '{relative_path}' does not exist in outputs directory. Planned action was 'modify'. Flagging for manual review.")
                  needs_manual_review.append(relative_path + f" (Needs Manual Action - Missing in outputs, planned modify - details in {step_output_filename})")
        else:
            print(f"Warning: Unknown action '{action}' for file '{relative_path}'. Flagging for manual review.")
            needs_manual_review.append(relative_path + f" (Unknown Action - details in {step_output_filename})")

    # 10. Final Report and Next Steps
    print("\n--- Plan Execution Summary ---")
    if applied_files:
        print("Files Automatically Created in outputs directory:")
        for f in applied_files:
            print(f"  - {f}")
    if needs_manual_review:
        print("Files Requiring Manual Action/Review:")
        for f in needs_manual_review:
            print(f"  - {f}")
    if not applied_files and not needs_manual_review:
        print("No files were created or flagged for manual review.")
        
    # Add guidance for incremental implementation if this was a code step
    if is_code_step:
        print("\n--- Next Steps for Incremental Implementation ---")
        print("1. Review the generated files in the outputs directory")
        print("2. For skeleton/placeholder files, use these steps to implement incrementally:")
        print("   a. Edit the .gcode-agent/outputs/<step>_output.md file to focus on one file at a time")
        print("   b. Run 'gcode-agent generate <step> --apply' again to implement the focused file")
        print("   c. Repeat until all necessary files are fully implemented")
        print("3. Move completed files to their final locations in your project structure")

    if not execution_success:
        print("\nWarning: One or more tool errors occurred during execution.")
        return False

    return True
