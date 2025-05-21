# gcode-agent: AI Agent CLI for SaaS Generation

`gcode-agent` is a Python command-line tool designed to facilitate the incremental and iterative generation of full-stack SaaS applications based on a predefined specification, utilizing Google's Gemini models.

It acts as an orchestrator, reading step-by-step specification **templates**, gathering context from the **actual outputs of previous steps**, and leveraging an LLM to generate plans for code creation and modification. It saves the output of each step to provide context for subsequent steps. It also provides an MCP (Model Context Protocol) server interface.

## Features

*   **Spec-Driven Generation:** Reads markdown specification **templates** (`spec/*.md`) to guide application generation for each step.
*   **Context-Aware & Incremental:** Builds context by using the actual outputs from previous steps when generating the current step. Saves the output of each step.
*   **Stateful Step Chaining:** Introduces a `next` command that intelligently executes the subsequent step in the generation sequence (step1 through step6), tracking progress in `config.json` via the `current_project_step` key.
*   **Iterative Development:** Generate application components step-by-step based on the spec templates and evolving context.
*   **File Creation and Modification:** When using `generate --apply` or `next --apply`, the agent can create new files or **modify existing files** directly within the `.gcode-agent/outputs/` directory based on the generated plan.
*   **Automated Python Linting:** Automatically runs `flake8` on generated or modified Python files (if `flake8` is installed and available in the system PATH) when using `generate --apply` or `next --apply`, and reports findings directly.
*   **Selective File Integration:** The `apply-to-workspace` command allows you to selectively copy generated or modified files from the agent's output directory to your main project workspace for integration.
*   **Organized Outputs:** Stores all generated and modified files in the `.gcode-agent/outputs/` directory, which can be excluded from git using the provided `.gitignore` entry.
*   **Gemini Integration:** Uses specified Gemini models (`gemini-1.5-pro`, `gemini-1.5-flash`, etc.) via the `google-generativeai` SDK.
*   **Plan-Based Execution:** Generates a plan for file modifications based on the current step's template and previous context.
*   **Configuration Management:** View and manage tool configuration (e.g., default model, `current_project_step`).
*   **MCP Server:** Exposes agent functionality (initialization, generation, config, spec resources) via the Model Context Protocol for integration with compatible clients.

## Setup

1.  **Clone the Repository (if applicable):**
    ```bash
    git clone <repository-url>
    cd gcode-agent-cli
    ```

2.  **Install Dependencies:**
    Create a virtual environment (recommended):
    ```bash
    python -m venv venv
    source venv/bin/activate # On Windows use `venv\Scripts\activate`
    ```
    Install required packages:
    ```bash
    pip install -r requirements.txt
    ```
    For Python linting, ensure `flake8` is installed:
    ```bash
    pip install flake8
    ```
    (Make sure `flake8` is then available in your system's PATH).

3.  **Set API Key:**
    You need a Google AI API key for Gemini. Set it as an environment variable:
    ```bash
    export GEMINI_API_KEY='your-google-ai-api-key'
    ```
    Alternatively, you can pass it using the `--api-key` flag with each command, but this is less secure and convenient.

4.  **Prepare Specification Templates:**
    The `init` command will generate initial specification files based on your problem description. However, it uses a set of **template** files to guide this generation process. By default, it looks for these templates in a `spec/` directory in your project's root. If this directory exists, ensure it contains your desired base templates (e.g., `step1-problem-definition.md`, `step2-ia-entities.md`, etc.). If it doesn't exist, the agent will use minimal built-in placeholders, which you should then customize. You can also specify a different template directory using the `--template-dir` option during initialization.

## Usage

Make the main script executable (if not installed):
```bash
chmod +x gcode_agent.py # Or however you run the agent
```

**1. Initialize Project:**

Generates initial specification files tailored to your project's problem description, creates the `.gcode-agent` directory structure (`spec`, `outputs`), and sets up a configuration file (`.gcode-agent/config.json`).

```bash
./gcode_agent.py init "High-level description of the problem your SaaS solves." [--template-dir <path>] [--model <model_name>] [--verbose]

# Example using default spec/ directory for templates:
./gcode_agent.py init "A platform for managing community gardening plots and sharing harvest data." --model gemini-1.5-flash-latest

# Example specifying a custom template directory:
./gcode_agent.py init "An AI-powered tool to summarize academic papers." --template-dir ../my-custom-templates -v
```
*   **`"problem_description"`**: **Required.** A quoted string describing the core problem your SaaS application aims to solve. This is used to customize the initial specification files.
*   `--template-dir <path>`: (Optional) Path to a directory containing the base markdown template files (`stepX-....md`). If not provided or invalid, it defaults to looking for a `spec/` directory in the current working directory. If neither is found, minimal placeholders are used for generation.
*   `--model <model_name>`: (Optional) Specify the Gemini model to use for generating the initial specs and store it in the config. Defaults to the globally set default model.
*   `--verbose` or `-v`: Show detailed output during initialization.

The command performs these actions:
1.  Determines the source directory for templates.
2.  Initializes a Gemini client.
3.  Generates customized specification files for each step and saves them to `.gcode-agent/spec/`.
4.  Creates the `.gcode-agent/outputs` directory.
5.  Creates `.gcode-agent/config.json`, storing:
    *   `problem_description`
    *   `template_directory` (path to the templates used)
    *   `model` (the model used for initialization)
    *   `current_step` (initially `None`, can be set via `config set`)
    *   `current_project_step` (initialized to `"step0"` to track overall project progress).

**2. Generate Specific Step Plan & Apply Changes (Manual Step Control):**

If you need to re-run a specific step or work out of sequence, use the `generate` command. It reads the template for the specified step, gathers context, generates a plan, and optionally applies it.

```bash
./gcode_agent.py generate <step_name> [--apply] [--model <model_name>] [--verbose]

# Examples:
# Generate step 1 plan (no previous context, saves plan to outputs)
./gcode_agent.py generate step1

# Re-generate step 4 plan, using context from steps 1-3 outputs, save plan,
# and attempt to create/modify files in .gcode-agent/outputs/
./gcode_agent.py generate step4 --apply --model gemini-1.5-pro-latest -v
```
*   `<step_name>`: Required name of the step to generate (e.g., `step1`, `step4`).
*   `--apply`: (Optional) If included, attempts to automatically create new files or **modify existing files** within the `.gcode-agent/outputs/` directory. Python files are linted with `flake8` if available.
*   `--model`: (Optional) Override the default/configured Gemini model for this run.
*   `--verbose` or `-v`: Show detailed output.

**3. Execute Next Step in Sequence (Recommended Workflow):**

The `next` command is the primary way to advance through the project. It automatically determines and executes the next step based on the `current_project_step` stored in `.gcode-agent/config.json`.

```bash
./gcode_agent.py next [--apply] [--model <model_name>] [--verbose]

# Examples:
# Assume 'init' has been run (current_project_step is "step0").

# Execute step1 and apply changes
./gcode_agent.py next --apply
# Agent identifies next step as "step1", generates plan, applies it.
# On success, config.json updates to current_project_step: "step1".

# Execute step2 and apply changes
./gcode_agent.py next --apply
# Agent identifies next step as "step2", generates plan, applies it.
# On success, config.json updates to current_project_step: "step2".
# ...and so on for subsequent steps.
```
*   `--apply`: (Optional) If included, attempts to automatically create or modify files in `.gcode-agent/outputs/` for the executed step. Python files are linted.
*   `--model <model_name>`: (Optional) Override the default or globally configured Gemini model for this specific step execution. The model specified in `config.json` is used by default.
*   `--verbose` or `-v`: Show detailed output.

Behavior:
*   Reads `current_project_step` from `.gcode-agent/config.json`.
*   Determines the next step in the predefined sequence (`step1` through `step6`).
*   Invokes the generation logic for that step (similar to `gcode-agent generate <next_step_name>`).
*   If the step completes successfully, it updates `current_project_step` in `config.json` to the step that was just executed.

**4. Apply File to Workspace:**

Copies a specific file from the agent's output directory (`.gcode-agent/outputs/`) to your main project workspace.

```bash
./gcode_agent.py apply-to-workspace <file_path_in_outputs> [--target-path <destination_path_in_project>]

# Example:
./gcode_agent.py apply-to-workspace services/user_service.py --target-path src/services/user_service.py
```
*   `<file_path_in_outputs>`: **Required.** Path of the file *within* `.gcode-agent/outputs/`.
*   `--target-path <destination_path_in_project>`: (Optional) Destination path. Defaults to the same relative path in CWD.

**5. Manage Configuration:**

View or update settings stored in `.gcode-agent/config.json`.

```bash
# List all settings
./gcode_agent.py config list

# Get a specific setting
./gcode_agent.py config get current_project_step

# Set an allowed setting (e.g., 'model', 'current_step', 'current_project_step')
./gcode_agent.py config set model gemini-1.5-flash-latest
./gcode_agent.py config set current_project_step step2
```

**6. Run as MCP Server:**

Starts an MCP server exposing agent functionality.

```bash
./gcode_agent.py serve-mcp [--host <ip_address>] [--port <port_number>]
```

## Iterative Development Workflow

The recommended workflow leverages the `next` command for sequential progress:

1.  **Initialize Project:**
    ```bash
    ./gcode_agent.py init "Your detailed problem description for the SaaS application."
    ```
    This sets `current_project_step` to `"step0"` in `.gcode-agent/config.json`.

2.  **Run Next Step:**
    ```bash
    ./gcode_agent.py next --apply 
    ```
    *   The agent identifies the next step (e.g., "step1" if current is "step0").
    *   It generates the plan for "step1", applies changes to `.gcode-agent/outputs/`, and runs linters.
    *   On success, `current_project_step` in `config.json` is updated (e.g., to "step1").

3.  **Review Outputs:**
    *   Examine the generated/modified files in `.gcode-agent/outputs/`.
    *   Check the console output for linting messages or other warnings from the agent.

4.  **Refine Current Step (If Necessary):**
    *   If "step1" (or the most recently completed step) needs further refinement *by the agent itself* (e.g., you want the LLM to try generating a file differently based on adjusted instructions):
        *   Manually edit the plan file for that step (e.g., `.gcode-agent/outputs/step1_output.md`). Adjust the plan instructions for the specific file(s) you want the agent to re-process.
        *   Re-run the *specific* step using the `generate` command:
            ```bash
            ./gcode_agent.py generate step1 --apply 
            ```
        *   The `next` command is for moving *forward* to a new, uncompleted step. The `generate` command is for re-processing a specific step.

5.  **Integrate into Project:**
    *   Once satisfied with a file in the `.gcode-agent/outputs/` directory, use the `apply-to-workspace` command to copy it into your main project structure:
    ```bash
    ./gcode_agent.py apply-to-workspace path/to/your/file_in_outputs.py --target-path path/to/your/project/file.py
    ```

6.  **Manual Integration & Testing:**
    *   After copying, manually integrate the new/updated code with the rest of your project.
    *   Run your project's tests, add new tests, and ensure everything works as expected.

7.  **Proceed to Next Step:**
    *   When ready to move to the next phase of generation (e.g., from "step1" to "step2"):
    ```bash
    ./gcode_agent.py next --apply
    ```
    *   The agent will execute "step2", and `current_project_step` will be updated accordingly.
    *   Repeat steps 3-7 for all subsequent steps in the project.

## Development Notes

*   **Manual Spec Refinement:** The generated specs in `.gcode-agent/spec` should also be reviewed and refined after the initial `init` command. These specs are crucial for guiding the agent.
*   **Context Building:** The agent automatically uses the saved outputs from previous steps (the `*_output.md` plan files) as context. The initial `problem_description` stored in the config is also used as context during generation steps.
*   **Output Organization:** All generated and modified files are first staged in the `.gcode-agent/outputs/` directory. This directory is excluded from git tracking by default.
*   **Prompt Engineering:** The quality of generated plans heavily depends on the prompts in `generate_command.py` and the content of the spec templates and previous outputs.
*   **Plan Parsing:** The system uses an LLM call to parse the generated plan text and extract file modifications into a JSON format.
*   **Error Handling:** Error handling can be improved.
*   **Testing:** See the `tests/` directory outline for unit/integration tests (implementation pending).

## Contributing

Contributions are welcome! Please see the [CONTRIBUTING.md](CONTRIBUTING.md) file for guidelines on how to report bugs, suggest enhancements, or submit pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
