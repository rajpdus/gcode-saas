# Agent Plan: Step 4 - Generate UI

## 1. Goal

To automatically generate a basic, functional User Interface (UI) based on the defined Information Architecture (IA) and Logical Data Model, providing standard CRUD operations for the core entities. The UI will use the predefined stack: React and shadcn/ui.

## 2. Input

*   Logical Data Model (Entities, Attributes, Relationships from Step 2)
*   Basic Information Architecture Outline (from Step 2)
*   (Implicit) API Contracts: While not fully defined until Step 5, the `FrontendAgent` needs to anticipate the basic CRUD API endpoints that the `BackendAgent` will create.
*   (Implicit) Authentication Flow: Basic understanding that authentication (likely Cognito) will be involved (details from `AuthAgent` come in Step 5).

## 3. Primary Agent(s) Involved

*   **`OrchestratorAgent`**: Manages the process.
*   **`FrontendAgent`**: Primary agent responsible for generating React code.
*   **`ArchitectureAgent`**: Provides IA context.

## 4. Process / Workflow

1.  **Input Transfer:** `OrchestratorAgent` provides the Logical Data Model and IA outline from `ArchitectureAgent` to the `FrontendAgent`.
2.  **Component Planning:** `FrontendAgent` analyzes the IA and entities to plan the required UI components:
    *   **Layout:** Basic application layout (e.g., sidebar navigation, main content area).
    *   **Pages/Views:** Identify necessary pages based on IA (e.g., Dashboard, Entity List page, Entity Detail page, Create/Edit Entity page).
    *   **CRUD Components:** Plan standard components for displaying lists (e.g., using `shadcn/ui` Table), viewing details, and forms for creating/editing entities (using `shadcn/ui` Input, Select, Button, etc.).
3.  **Code Generation:** `FrontendAgent` generates the React application structure and code:
    *   Sets up a standard React project (e.g., using Vite or Create React App).
    *   Installs necessary dependencies (`react`, `react-dom`, `react-router-dom`, `shadcn/ui` related packages) in `dependencies`.
    *   Installs development dependencies (e.g., testing libraries, linters) in `devDependencies`.
    *   Generates reusable UI components based on `shadcn/ui`.
    *   Generates page components and sets up basic routing (`react-router-dom`).
    *   Generates forms for entity creation/editing based on entity attributes.
    *   Generates basic data display components (tables, detail views).
    *   Creates placeholder functions/hooks for API calls (to be fully implemented in Step 5).
    *   Sets up basic state management for UI interactions.
4.  **Placeholder Integration:** Includes placeholders for authentication logic (e.g., login forms, conditional rendering for protected routes) and API integration points.
5.  **Build Configuration:** Generates/updates `package.json` with necessary build and development scripts.
6.  **Validation:** `OrchestratorAgent` performs basic structural checks on the generated frontend code (e.g., project structure, presence of key components).

## 5. Output

*   **Frontend Application Source Code:** A complete, runnable (though not yet fully functional) React project directory including:
    *   Component files (.jsx/.tsx)
    *   Page files
    *   Routing configuration
    *   Basic state management setup
    *   CSS / styling setup (leveraging `shadcn/ui` theming)
    *   `package.json` and other build configuration files.
*   **List of Anticipated API Endpoints:** A list of the CRUD API endpoints the generated UI expects the backend to provide.

## 6. Best Practices / Constraints Enforcement

*   **Component-Based Architecture:** Generated code MUST follow React best practices for component design.
*   **Framework Constraint:** MUST use React and `shadcn/ui` as specified.
*   **Dependency Segregation:** Development tools (linters, test runners) MUST be listed in `devDependencies`, while runtime libraries are in `dependencies` in `package.json`.
*   **Standard CRUD:** The generated UI primarily focuses on standard CRUD operations for the defined entities.
*   **Modularity:** Code should be organized logically into components and potentially feature folders.
*   **Placeholders:** Clearly mark areas requiring backend API integration and authentication logic from Step 5.
*   **Responsiveness (Basic):** Leverage `shadcn/ui`'s responsive capabilities for a basic level of adaptability. 