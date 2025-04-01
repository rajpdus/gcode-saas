import os
import shutil
import sys
import json

# Import the Gemini client
from ..core.gemini_client import GeminiClient

AGENT_DIR = ".gcode-agent"
SPEC_SUBDIR = "spec"
OUTPUT_SUBDIR = "outputs"
CONFIG_FILE = "config.json"

# Map of spec templates to generate
SPEC_TEMPLATES = {
    "step1-problem-definition.md": "Generate a detailed problem definition based on the high-level description",
    "step2-ia-entities.md": "Define information architecture and entities for the SaaS application",
    "step3-dynamodb-model.md": "Design DynamoDB tables and access patterns",
    "step4-generate-ui.md": "Design the UI/UX for the SaaS application",
    "step5-integrate-backend-auth.md": "Design authentication and authorization",
    "step6-prepare-deployment.md": "Prepare deployment strategy on AWS",
    "agent-plan.md": "Overall agent plan for the SaaS application"
}

def get_template_content(template_name, template_dir):
    """
    Get the content of a template file.
    If the file doesn't exist or cannot be read, return a minimal placeholder.
    
    Args:
        template_name: The name of the template file
        template_dir: The directory containing template files
        
    Returns:
        The content of the template file or a minimal placeholder.
    """
    template_path = os.path.join(template_dir, template_name)
    
    # Try to read the template from the provided template directory
    if os.path.exists(template_path):
        try:
            with open(template_path, 'r') as f:
                return f.read()
        except Exception as e:
            print(f"\nWarning: Could not read template file {template_path}: {e}", file=sys.stderr)
    else:
        print(f"\nWarning: Template file not found: {template_path}", file=sys.stderr)

    # If the template file doesn't exist or couldn't be read, return a minimal placeholder
    print(f"Using minimal placeholder for {template_name}.")
    return f"""# {template_name}

This is a minimal placeholder template for {template_name} because the original could not be found or read from '{template_dir}'.

Please customize this file with appropriate sections and content based on the project's needs.
"""

def generate_spec_file(client, problem_description, template_name, template_dir, prompt_instruction):
    """
    Generate a customized spec file using the Gemini client.
    
    Args:
        client: The GeminiClient instance
        problem_description: The high-level problem description
        template_name: The name of the template file to generate
        template_dir: The directory containing template files
        prompt_instruction: The instruction for generating this specific template
        
    Returns:
        The generated content for the spec file
    """
    # Get the template content
    template_content = get_template_content(template_name, template_dir)
    
    # Special handling for step1-problem-definition
    if template_name == "step1-problem-definition.md":
        prompt = f"""
You are an AI agent tasked with creating a specification file for a SaaS application.

The high-level problem description for the application is:
"{problem_description}"

Your task is to create a detailed problem definition based on this high-level description.

Here is the template structure to follow:
```
{template_content}
```

Based on the problem description, generate a customized version of this specification file that:
1. Maintains the same structure but tailors the content specifically to this problem domain
2. Includes the exact high-level problem description provided by the user in the "Output" section under "Validated Problem Statement"
3. Expands on this description to provide more context, target audience details, and core objectives
4. Keeps all sections and headings from the template

The content should be clear, specific, and actionable.
"""
    else:
        # Construct prompt for generating other spec files
        prompt = f"""
You are an AI agent tasked with creating a specification file for a SaaS application.

The high-level problem description for the application is:
"{problem_description}"

Your task is to: {prompt_instruction}

Here is the template structure to follow:
```
{template_content}
```

Based on the problem description, generate a customized version of this specification file that maintains the same structure but tailors the content specifically to this problem domain. 
Keep all sections and headings from the template but adapt the examples, suggestions, and details to be relevant to the specific problem described above.
The content should be clear, specific, and actionable.
"""

    try:
        # Generate content using the Gemini client
        generated_content = client.generate_content(prompt)
        return generated_content
    except Exception as e:
        print(f"Error generating content for {template_name}: {e}", file=sys.stderr)
        # Return a simple error template as fallback
        return f"""# Error Generating {template_name}

Unfortunately, there was an error generating this template: {str(e)}

## Manual Action Required

Please modify this file with the appropriate content for {template_name}.

The high-level problem description was:
"{problem_description}"
"""

def handle_init(args):
    """Handles the initialization of the gcode-agent project with generated spec files."""
    problem_description = args.problem_description
    user_template_dir = args.template_dir # Directory specified by the user or default "spec"
    verbose = args.verbose
    api_key = args.api_key
    model = args.model
    
    effective_template_dir = None
    template_source_message = ""

    # 1. Check if user-provided template directory is valid
    if os.path.isdir(user_template_dir):
        effective_template_dir = user_template_dir
        template_source_message = f"Using user-provided template directory: {effective_template_dir}"
    else:
        if user_template_dir != "spec": # Only warn if it wasn't the default
            print(f"Warning: User-provided template directory not found: {user_template_dir}")
        
        # 2. Fallback: Check for root spec/ directory
        root_spec_dir = "../spec" 
        if os.path.isdir(root_spec_dir):
            effective_template_dir = root_spec_dir
            template_source_message = f"Using default template directory at root: {effective_template_dir}"
        else:
             # 3. No valid template directory found
             effective_template_dir = "." # Set placeholder dir, get_template_content will handle missing files
             template_source_message = "Warning: No valid template directory found. Specifications will be generated using minimal placeholders."

    print(template_source_message)
    if verbose and effective_template_dir != "." and os.path.isdir(effective_template_dir):
        template_files = [f for f in os.listdir(effective_template_dir) if f.endswith('.md')]
        print(f"Found template files in {effective_template_dir}: {', '.join(template_files)}")


    # --- Overwrite Check ---
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
        # --- Initialize Gemini Client ---
        if verbose:
            print(f"Initializing Gemini client with model: {model}")
        
        print("\nGenerating customized specifications based on problem description...")
        print(f"Problem: \"{problem_description}\"")
        
        client = GeminiClient(
            api_key=api_key,
            model_name=model,
            verbose=verbose
        )
        
        # --- Create Directories ---
        if verbose:
            print(f"Creating agent directory: {AGENT_DIR}")
        os.makedirs(AGENT_DIR, exist_ok=True)

        if verbose:
            print(f"Creating spec directory: {target_spec_dir}")
        os.makedirs(target_spec_dir, exist_ok=True)

        # Create the outputs directory
        if verbose:
            print(f"Creating outputs directory: {target_output_dir}")
        os.makedirs(target_output_dir, exist_ok=True)

        # --- Generate Spec Files ---
        successful_generations = 0
        total_templates = len(SPEC_TEMPLATES)
        
        print("\nGenerating specifications - this may take a few moments...")
        
        for template_name, prompt_instruction in SPEC_TEMPLATES.items():
            if verbose:
                print(f"Generating spec file: {template_name}")
            else:
                print(f"Generating {template_name}...", end="", flush=True)
            
            # Use the determined effective_template_dir
            generated_content = generate_spec_file(
                client=client,
                problem_description=problem_description,
                template_name=template_name,
                template_dir=effective_template_dir, 
                prompt_instruction=prompt_instruction
            )
            
            # Save the generated spec file
            target_file_path = os.path.join(target_spec_dir, template_name)
            if verbose:
                print(f"Saving generated spec file to: {target_file_path}")
            
            with open(target_file_path, 'w') as f:
                f.write(generated_content)
            
            successful_generations += 1
            if not verbose:
                print(" Done")

        # --- Create Config File ---
        config_path = os.path.join(AGENT_DIR, CONFIG_FILE)
        config_data = {
            "problem_description": problem_description,
            "template_directory": os.path.abspath(effective_template_dir) if effective_template_dir != "." else None,
            "current_step": None, # Track generation progress later
            "model": model # Store the model used during init
        }
        if verbose:
            print(f"Creating config file: {config_path}")
        with open(config_path, 'w') as f:
            json.dump(config_data, f, indent=4)

        # --- Final Output ---
        print(f"\ngcode-agent initialized successfully in '{AGENT_DIR}'")
        print(f"Generated {successful_generations}/{total_templates} specification files customized for:")
        print(f"  \"{problem_description}\"")
        print(f"Used template source: {template_source_message}")
        print("\nNext steps:")
        print("  1. Review the specifications in the .gcode-agent/spec/ directory")
        print("  2. Run 'gcode-agent generate step1' to start implementing the solution")
        return True # Indicate success

    except Exception as e:
        print(f"Error during initialization: {e}", file=sys.stderr)
        # Clean up partially created directory if error occurred
        if os.path.exists(AGENT_DIR):
            try:
                shutil.rmtree(AGENT_DIR)
            except OSError as cleanup_e:
                print(f"Error during cleanup: {cleanup_e}", file=sys.stderr)
        return False
