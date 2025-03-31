# Example: Generating a ToDo Application with gcode-agent

This document outlines the steps to generate a sample ToDo application using the `gcode-agent` CLI tool.

## Prerequisites

1.  **gcode-agent Setup:** Ensure `gcode-agent` is installed and configured according to the main `README.md` (dependencies installed, `GEMINI_API_KEY` set).
2.  **ToDo App Specification:** You must have a directory containing the detailed step-by-step specifications for your ToDo application. Let's assume this directory is named `../todo-specs` relative to the `gcode-agent-cli` directory, and it contains files like:
    *   `step1-definition.md` (Problem, Audience, Core Features like add, view, complete, delete tasks)
    *   `step2-entities.md` (Entities: `User`, `Task`; Attributes: `taskId`, `userId`, `description`, `isComplete`, `dueDate`)
    *   `step3-datamodel.md` (DynamoDB design for Tasks, maybe user profiles)
    *   `step4-ui.md` (React UI design using shadcn/ui for listing, adding, updating tasks)
    *   `step5-backend.md` (Chalice backend API endpoints for CRUD operations on tasks, Cognito auth integration)
    *   `step6-deploy.md` (CloudFormation for backend, frontend hosting, CI/CD pipeline)
    *(These spec files need to be created by you or another process, detailing the requirements for each step according to the agent plan structure.)*
3.  **Project Directory:** You should be in the directory where you want the *generated ToDo application code* to reside (e.g., `my-todo-app/`). The `gcode-agent` tool will create/modify files relative to your current working directory.

## Steps

Let's assume you are in an empty directory `my-todo-app` where you want the code generated.

1.  **Initialize `gcode-agent` for the Project:**
    Tell `gcode-agent` where your ToDo app specification templates are. This copies the specs into `.gcode-agent/spec` and creates `.gcode-agent/outputs` and `.gcode-agent/config.json`.
    ```bash
    # Run from within my-todo-app/ directory
    # Adjust the path to your gcode-agent executable and spec directory as needed
    ../gcode-agent-cli/gcode_agent.py init ../todo-specs --model gemini-1.5-flash-latest
    ```
    *   Initializes the agent's state and structure (`.gcode-agent/`) for this project.

2.  **Generate Step 1 (Definition Validation - Optional):**
    Generates the initial plan/output based on the Step 1 template.
    ```bash
    ../gcode-agent-cli/gcode_agent.py generate step1
    ```
    *   Reads the template `.gcode-agent/spec/step1-definition.md`.
    *   Prompts Gemini based on the template.
    *   Prints the generated plan/output.
    *   Saves this output to `.gcode-agent/outputs/step1_output.md` for future context.
    *   Review the output.

3.  **Generate Step 2 (Entities & IA Plan):**
    Generates the plan based on the Step 2 template and the saved output from Step 1.
    ```bash
    ../gcode-agent-cli/gcode_agent.py generate step2
    ```
    *   Reads the template `.gcode-agent/spec/step2-entities.md`.
    *   Reads the context from `.gcode-agent/outputs/step1_output.md`.
    *   Prompts Gemini using both the template and the previous context.
    *   Prints the generated plan.
    *   Saves this output to `.gcode-agent/outputs/step2_output.md`.
    *   Review the output.

4.  **Generate Step 3 (Data Model Plan & Apply):**
    Generates the plan using the Step 3 template and context from Steps 1 & 2. Attempts to create new files.
    ```bash
    # Use --apply to attempt automatic creation of new files
    ../gcode-agent-cli/gcode_agent.py generate step3 --apply
    ```
    *   Reads template `.gcode-agent/spec/step3-datamodel.md`.
    *   Reads context from `.gcode-agent/outputs/step1_output.md` and `step2_output.md`.
    *   Prompts Gemini.
    *   Prints the generated plan.
    *   Saves the plan to `.gcode-agent/outputs/step3_output.md`.
    *   **Attempts to automatically create** new files suggested in the plan.
    *   **Action Required:** Review the summary. Verify file creation. Handle errors or manual modifications.

5.  **Generate Step 4 (UI Plan & Apply):**
    Generates the UI plan using the Step 4 template and context from Steps 1-3.
    ```bash
    ../gcode-agent-cli/gcode_agent.py generate step4 --apply --verbose
    ```
    *   Reads template `.gcode-agent/spec/step4-ui.md`.
    *   Reads context from `step1_output.md`, `step2_output.md`, `step3_output.md`.
    *   Prompts Gemini.
    *   Prints the plan.
    *   Saves the plan to `.gcode-agent/outputs/step4_output.md`.
    *   **Attempts to automatically create** new frontend files.
    *   **Action Required:** Review summary, verify creation, handle manual steps.

6.  **Generate Step 5 (Backend Plan & Apply):**
    Generates the backend plan using the Step 5 template and context from Steps 1-4.
    ```bash
    ../gcode-agent-cli/gcode_agent.py generate step5 --apply
    ```
    *   Reads template `.gcode-agent/spec/step5-backend.md`.
    *   Reads context from previous outputs.
    *   Prompts Gemini.
    *   Prints the plan.
    *   Saves the plan to `.gcode-agent/outputs/step5_output.md`.
    *   **Attempts to automatically create** new files.
    *   **Flags modifications** for manual review.
    *   **Action Required:** Review summary, verify creation, manually merge modifications.

7.  **Generate Step 6 (Deployment Plan & Apply):**
    Generates the deployment plan using the Step 6 template and context from Steps 1-5.
    ```bash
    ../gcode-agent-cli/gcode_agent.py generate step6 --apply
    ```
    *   Reads template `.gcode-agent/spec/step6-deploy.md`.
    *   Reads context from previous outputs.
    *   Prompts Gemini.
    *   Prints the plan.
    *   Saves the plan to `.gcode-agent/outputs/step6_output.md`.
    *   **Attempts to automatically create** new files.
    *   **Flags modifications** for manual review.
    *   **Action Required:** Review summary, verify creation, manually merge modifications.

8.  **Review and Refine:**
    After generating all steps (and applying changes where possible/desired), manually review the complete code structure and files in your `my-todo-app` directory. You will likely need to:
    *   Install dependencies (`pip install -r backend/requirements.txt`, `npm install` in `frontend/`).
    *   Run linters/formatters.
    *   Debug integration issues.
    *   Manually apply any changes that were flagged during the `--apply` process.
    *   Implement the actual logic for deployment scripts.
    *   Fill in any gaps.

## Summary

The `gcode-agent` facilitates generating the *plan* and *initial code* based on your specification templates and the actual outputs from previous generation steps. Using the `--apply` flag allows the agent to automatically **create new files**. However, **modifications to existing files still require manual review and merging**. This iterative, context-aware process helps scaffold the application more effectively while maintaining user control. 