# gcode-agent: AI Agent CLI for SaaS Generation

`gcode-agent` is a Python command-line tool designed to facilitate the incremental and iterative generation of full-stack SaaS applications based on a predefined specification, utilizing Google's Gemini models.

It acts as an orchestrator, reading step-by-step specification **templates**, gathering context from the **actual outputs of previous steps**, and leveraging an LLM to generate plans for code creation and modification. It saves the output of each step to provide context for subsequent steps. It also provides an MCP (Model Context Protocol) server interface.

## Features

*   **Spec-Driven Generation:** Reads markdown specification **templates** (`spec/*.md`) to guide application generation for each step.
*   **Context-Aware & Incremental:** Builds context by using the actual outputs from previous steps when generating the current step. Saves the output of each step.
*   **Iterative Development:** Generate application components step-by-step based on the spec templates and evolving context.
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
    Ensure you have a directory containing your step-by-step application specification **templates** in Markdown format (e.g., `../spec/step1-problem-definition.md`, `../spec/step2-ia-entities.md`, etc.). These act as guides for each step.

## Usage

Make the main script executable:
```bash
chmod +x gcode_agent.py
```

**1. Initialize Project:**

Copies the specification templates into `.gcode-agent/spec`, creates the `.gcode-agent/outputs` directory for storing step results, and creates a configuration file.

```bash
./gcode_agent.py init <path_to_your_spec_template_directory>

# Example:
./gcode_agent.py init ../spec --model gemini-1.5-flash-latest
```
*   `<path_to_your_spec_template_directory>`: Required path to the directory containing your `stepX-....md` template files.
*   `--model`: (Optional) Specify the Gemini model to store in the config during init.

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
8.  If `--apply` is used, attempts to *create* new files via the `edit_file` tool.
9.  Prints a summary indicating which files were created (if `--apply` used) and which need manual review (modifications or new files without `--apply`).

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

*   **Manual Modification:** Modifications to existing files *always* require manual review and merging, even with `--apply`.
*   **Context Building:** The agent automatically uses the saved outputs from previous steps as context.
*   **Prompt Engineering:** The quality of generated plans heavily depends on the prompts in `generate_command.py` and the content of the spec templates and previous outputs.
*   **Plan Parsing:** The regex in `plan_parser.py` assumes a certain output format from the LLM. It might need adjustments based on observed model outputs.
*   **Error Handling:** Error handling can be improved, especially for MCP tool calls and file operations.
*   **Testing:** See the `tests/` directory outline for unit/integration tests (implementation pending).

## Contributing

Contributions are welcome! Please see the [CONTRIBUTING.md](CONTRIBUTING.md) file for guidelines on how to report bugs, suggest enhancements, or submit pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
