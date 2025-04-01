# gcode-agent: AI Agent CLI for SaaS Generation

`gcode-agent` is a Python command-line tool designed to facilitate the incremental and iterative generation of full-stack SaaS applications based on a predefined specification, utilizing Google's Gemini models.

It acts as an orchestrator, reading step-by-step specification **templates**, gathering context from the **actual outputs of previous steps**, and leveraging an LLM to generate plans for code creation and modification. It saves the output of each step to provide context for subsequent steps. It also provides an MCP (Model Context Protocol) server interface.

## Features

*   **Spec-Driven Generation:** Reads markdown specification **templates** (`spec/*.md`) to guide application generation for each step.
*   **Context-Aware & Incremental:** Builds context by using the actual outputs from previous steps when generating the current step. Saves the output of each step.
*   **Iterative Development:** Generate application components step-by-step based on the spec templates and evolving context.
*   **Incremental File Generation:** Intelligently generates code in phases - focusing on structure first, then implementation details. Automatically truncates large files and prioritizes essential components.
*   **Organized Outputs:** Stores all generated files in the `.gcode-agent/outputs/` directory, which can be excluded from git using the provided `.gitignore` entry.
*   **Gemini Integration:** Uses specified Gemini models (`gemini-1.5-pro`, `gemini-1.5-flash`, etc.) via the `google-generativeai` SDK.
*   **Plan-Based Execution:** Generates a plan for file modifications based on the current step's template and previous context.
*   **Tool Use (with `--apply`):** Parses the generated plan and automatically creates *new* files using the `edit_file` tool when the `--apply` flag is used.
*   **Manual Modification:** Flags modifications to *existing* files for manual review and merging, even with `--apply`.
*   **Configuration Management:** View and manage tool configuration (e.g., default model).
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

Generates initial specification files tailored to your project's problem description, creates the `.gcode-agent` directory structure (`spec`, `outputs`), and sets up a configuration file.

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
1.  Determines the source directory for templates (user-provided, root `spec/`, or fallback).
2.  Initializes a Gemini client.
3.  For each standard step (`step1` to `step6`, plus `agent-plan.md`):
    *   Reads the corresponding template file from the determined source directory (or uses a minimal placeholder if not found).
    *   Constructs a prompt asking the LLM to customize the template based on the provided `problem_description`.
    *   Generates the customized content using the Gemini model.
    *   Saves the generated content to `.gcode-agent/spec/<step_name>.md`.
4.  Creates the `.gcode-agent/outputs` directory.
5.  Creates `.gcode-agent/config.json`, storing the `problem_description`, the path to the template directory used (if any), and the `model`.

**2. Generate Step Plan:**

Reads the template for the specified step, reads the outputs from all preceding steps (for context), prompts Gemini to generate a plan, saves the plan as the output for the current step, and optionally attempts to apply the plan.

```bash
./gcode_agent.py generate <step_name> [--apply] [--model <model_name>] [--verbose]

# Examples:
# Generate step 1 (no previous context, saves output)
./gcode_agent.py generate step1

# Generate step 4, using context from steps 1-3 outputs, save output, attempt to apply
./gcode_agent.py generate step4 --apply --model gemini-1.5-pro-latest -v
```
*   `<step_name>`: Required name of the step to generate (e.g., `step1`, `step4`).
*   `--apply`: (Optional) If included, attempts to automatically create *new* files suggested in the plan. Modifications to existing files are *always* flagged for manual review.
*   `--model`: (Optional) Override the default/configured Gemini model for this run.
*   `--verbose` or `-v`: Show detailed output.

The command performs these actions:
1.  Reads the template for `<step_name>` from `.gcode-agent/spec/`.
2.  Reads outputs from previous steps (`step1_output.md` to `stepN-1_output.md`) from `.gcode-agent/outputs/`.
3.  Constructs a prompt containing the previous outputs and the current step template.
4.  Calls the Gemini model to generate a plan.
5.  Prints the generated plan.
6.  Saves the plan to `.gcode-agent/outputs/<step_name>_output.md`.
7.  Parses the plan for file actions.
8.  If `--apply` is used:
    - For code files, it implements an incremental approach, focusing on structure over implementation details
    - Files are sorted by priority (documentation first, then essential code structure)
    - Large code files are automatically truncated to avoid overwhelming output
    - All generated files are created in the `.gcode-agent/outputs/` directory
9.  Prints a summary indicating which files were created (if `--apply` used) and which need manual review, along with guidance for incremental implementation.

**3. Manage Configuration:**

View or update settings stored in `.gcode-agent/config.json`.

```bash
# List all settings
./gcode_agent.py config list

# Get a specific setting
./gcode_agent.py config get model

# Set an allowed setting (currently 'model' or 'current_step')
./gcode_agent.py config set model gemini-1.5-flash-latest
./gcode_agent.py config set current_step step3
```

**4. Run as MCP Server:**

Starts an MCP server exposing agent functionality.

```bash
./gcode_agent.py serve-mcp [--host <ip_address>] [--port <port_number>]

# Example:
./gcode_agent.py serve-mcp --port 8080
```
*   `--host`: (Optional) Host address to bind to (default: `127.0.0.1`).
*   `--port`: (Optional) Port to listen on (default: `8000`).

Ensure `GEMINI_API_KEY` is set in the environment where the server runs.

Connect using an MCP-compatible client (e.g., Claude Desktop). The server exposes:
*   **Tools:** `initialize_project`, `generate_step`, `get_config_value`, `set_config_value`.
*   **Resources:** `spec://<filename>.md` (e.g., `spec://step1-problem-definition.md`).

## Development Notes

*   **Manual Modification:** Modifications to existing files *always* require manual review and merging, even with `--apply`. The generated specs in `.gcode-agent/spec` should also be reviewed and refined after initialization.
*   **Context Building:** The agent automatically uses the saved outputs from previous steps as context. The initial `problem_description` stored in the config is also used as context during generation steps.
*   **Incremental Generation:** The system is designed to generate code in phases - focusing first on structure and essential files, then implementation details in subsequent runs. This is particularly beneficial for large applications.
*   **Output Organization:** All generated files are stored in the `.gcode-agent/outputs/` directory, which is excluded from git tracking via the `.gitignore` entry. Files can be reviewed there before moving to their final locations.
*   **Prompt Engineering:** The quality of generated plans heavily depends on the prompts in `generate_command.py` and the content of the spec templates and previous outputs. Both the initial plan generation and the subsequent plan parsing rely on effective prompting.
*   **Plan Parsing:** The system uses a second LLM call to parse the generated plan text and extract file modifications into a JSON format. This is handled within `generate_command.py` and is generally more robust than regex-based approaches.
*   **Error Handling:** Error handling can be improved, especially for MCP tool calls, file operations, and JSON parsing of LLM outputs.
*   **Testing:** See the `tests/` directory outline for unit/integration tests (implementation pending).

## Contributing

Contributions are welcome! Please see the [CONTRIBUTING.md](CONTRIBUTING.md) file for guidelines on how to report bugs, suggest enhancements, or submit pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
