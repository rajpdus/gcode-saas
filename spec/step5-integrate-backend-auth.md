# Agent Plan: Step 5 - Integrate Backend & Auth

## 1. Goal

To generate the backend API using Chalice, integrate it with the DynamoDB data model, implement Cognito authentication, and connect the generated frontend UI to this backend, enabling full CRUD functionality and secure user access.

## 2. Input

*   Physical DynamoDB Data Model & CloudFormation Snippets (from Step 3)
*   Data Access Pattern Code Examples (from Step 3)
*   **OpenSearch Requirement Flag** (from Step 3)
*   Frontend Application Source Code (from Step 4)
*   List of Anticipated API Endpoints (from Step 4)
*   (Requires generation first) Cognito CloudFormation Snippets & Integration Details (from `AuthAgent` executing its Step 5 tasks)
*   API Contracts (refined from anticipated endpoints, potentially formalized by `ArchitectureAgent`)

## 3. Primary Agent(s) Involved

*   **`OrchestratorAgent`**: Manages the process, coordinates dependencies between agents.
*   **`BackendAgent`**: Generates Chalice API code, integrates DB and Auth.
*   **`AuthAgent`**: Generates Cognito resources and provides integration logic.
*   **`FrontendAgent`**: Updates frontend code to integrate with the real API and Auth.
*   **`InfrastructureAgent`**: Provides necessary IAM permissions for the backend Lambda function(s).
*   **`DatabaseAgent`**: Provides DB details.

## 4. Process / Workflow

1.  **Dependency Coordination:** `OrchestratorAgent` ensures necessary inputs are available, including the **OpenSearch Requirement Flag**. It triggers `AuthAgent` to generate Cognito resources and integration details *first* if not already done.
2.  **Backend API Generation (`BackendAgent`)**:
    *   Receives DynamoDB details (table names, access patterns) from `DatabaseAgent`.
    *   Receives Cognito details (User Pool ID, validation logic) from `AuthAgent`.
    *   Receives API contracts/endpoint list.
    *   Generates Chalice `app.py` defining API routes for CRUD operations based on contracts.
    *   **CORS Configuration:** Explicitly configures CORS in `app.py` (e.g., `app.api.cors = True` or more specific configuration using `CORSConfig`) to allow requests from expected frontend origins (potentially parameterized via environment variables later).
    *   Implements route handlers (Lambda functions) using Python.
    *   Integrates DynamoDB operations using `boto3` and access patterns from `DatabaseAgent`.
    *   Implements request validation (using Chalice features or Pydantic).
    *   Integrates Cognito token validation using JWT libraries or Chalice authorizers, applying authorization logic to routes.
    *   **OpenSearch Integration (Conditional):** If the **OpenSearch Requirement Flag** is true:
        *   Generates separate Lambda function code (potentially outside Chalice, e.g., in `backend/lambda/indexer.py`) responsible for processing DynamoDB Stream events and indexing/updating data in OpenSearch.
        *   Adds necessary OpenSearch client libraries (`opensearch-py`) to `requirements.txt`.
        *   Modifies backend CRUD operations (or uses DynamoDB Streams) to ensure data consistency between DynamoDB and OpenSearch.
    *   Implements structured logging and error handling.
    *   Generates/updates `requirements.txt` including `boto3`, `chalice`, JWT libraries, etc., and conditionally `opensearch-py`.
    *   Generates `requirements-dev.txt` including testing tools (`pytest`) and linters (`flake8`, `bandit`).
3.  **IAM Permission Granting (`InfrastructureAgent`)**:
    *   Receives requests from `BackendAgent` (via `OrchestratorAgent`) for necessary permissions (e.g., DynamoDB access, Cognito access).
    *   **OpenSearch Permissions (Conditional):** If OpenSearch is used, receives request for permissions to access the OpenSearch domain and potentially DynamoDB Stream read permissions for the indexer Lambda.
    *   Generates/updates the IAM Role CloudFormation snippet for the Chalice Lambda function(s) and the separate OpenSearch indexer Lambda (if applicable), adhering to least privilege.
4.  **Frontend Integration (`FrontendAgent`)**:
    *   Receives the final API endpoint URLs (once deployed or determined by Chalice/API Gateway configuration).
    *   Receives Cognito configuration details (User Pool ID, Client ID) and integration snippets from `AuthAgent`.
    *   Updates the React code generated in Step 4:
        *   Replaces placeholder API calls with actual `fetch` or `axios` calls to the backend endpoints.
        *   Integrates authentication using AWS Amplify UI library or similar, handling login, signup, logout, and secure API calls with tokens.
        *   Implements protected routes based on authentication status.
        *   Connects UI components (forms, tables) to the data fetched from the API.
5.  **Validation & Testing (`QualityAgent` - Optional but Recommended)**:
    *   Generates basic unit tests for Chalice route logic.
    *   Generates basic integration tests that call the API endpoints (requires local or deployed setup).
    *   Runs linters (`flake8`, `eslint`).
6.  **Orchestrator Review:** `OrchestratorAgent` checks for consistency between backend routes, frontend calls, and authentication integration.

## 5. Output

*   **Updated Backend Application Source Code:** Complete Chalice project (`app.py`, `chalicelib/`, `requirements.txt`) with DB and Auth integration. Conditionally includes OpenSearch indexer Lambda code (`backend/lambda/indexer.py`).
*   **Updated Frontend Application Source Code:** React project with integrated API calls and Cognito authentication.
*   **Updated CloudFormation Snippets:** IAM Role definition(s) for the Chalice Lambda function(s) and conditional OpenSearch indexer Lambda, including necessary permissions.
*   **(From `AuthAgent`) CloudFormation Snippets:** Cognito resource definitions.

## 6. Best Practices / Constraints Enforcement

*   **RESTful APIs:** Backend API MUST follow REST principles.
*   **Secure Integration:** Cognito integration MUST be implemented securely (token validation). Frontend MUST send tokens correctly.
*   **Explicit CORS:** Backend MUST configure CORS appropriately for expected frontend origins.
*   **Dependency Segregation:** Development dependencies (testing, linting) MUST be in `requirements-dev.txt`, separate from runtime `requirements.txt`.
*   **Input Validation:** Backend MUST validate all incoming request data.
*   **Least Privilege:** IAM Role for backend MUST have minimal permissions.
*   **Stack Constraints:** MUST use Chalice (Python), DynamoDB, Cognito, React.
*   **Error Handling:** Implement consistent error handling in backend and frontend.
*   **Modularity:** Backend code in `chalicelib/` should be modular. 