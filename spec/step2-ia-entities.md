# Agent Plan: Step 2 - Define Information Architecture & Entities

## 1. Goal

To translate the validated problem statement and target audience profile into a structured Information Architecture (IA) and identify the core data Entities the application will manage.

## 2. Input

*   Validated Problem Statement (from Step 1)
*   Target Audience Profile (from Step 1)
*   High-Level Core Objectives/Features (from Step 1)

## 3. Primary Agent(s) Involved

*   **`OrchestratorAgent`**: Manages the process, interacts with the user if needed.
*   **`ArchitectureAgent`**: Primary agent responsible for defining IA and entities.

## 4. Process / Workflow

1.  **Input Analysis:** The `OrchestratorAgent` provides the validated outputs from Step 1 to the `ArchitectureAgent`.
2.  **Entity Identification:** The `ArchitectureAgent` analyzes the problem statement, objectives, and audience profile to identify key nouns and concepts that represent the core data **Entities** the application needs to manage (e.g., `User`, `Product`, `Order`, `Document`, `Task`).
    *   It may ask clarifying questions via the `OrchestratorAgent` if the inputs are ambiguous regarding entities.
3.  **Attribute Definition:** For each identified Entity, the `ArchitectureAgent` proposes essential **Attributes** (properties or fields) based on the problem description and objectives (e.g., `User` entity might have `userId`, `email`, `name`, `creationDate`).
4.  **Relationship Mapping:** The `ArchitectureAgent` identifies and defines the primary **Relationships** between entities (e.g., a `User` *places* multiple `Orders`; an `Order` *contains* multiple `Products`). It defines the cardinality (one-to-one, one-to-many, many-to-many).
5.  **Information Architecture (IA) Sketch:** Based on entities, attributes, and relationships, the `ArchitectureAgent` proposes a basic IA, outlining how information might be structured and navigated within the application (e.g., a user dashboard showing their orders, a product listing page).
6.  **Output Formulation:** The `ArchitectureAgent` structures the identified entities, attributes, and relationships into a clear, logical format (e.g., list, simple diagram description).
7.  **Validation & Refinement (Internal/User):**
    *   The `OrchestratorAgent` reviews the proposed IA and entities for consistency with Step 1 outputs.
    *   Optionally, the `OrchestratorAgent` may present the proposed entities and key attributes/relationships to the user for validation or refinement, especially if complex or ambiguous.

## 5. Output

*   **Logical Data Model:**
    *   List of core **Entities**.
    *   For each Entity, a list of key **Attributes**.
    *   Description of primary **Relationships** between Entities, including cardinality.
*   **Basic Information Architecture Outline:** A high-level description of how information will be organized and presented to the user.

## 6. Best Practices / Constraints Enforcement

*   Focus on core entities required for the MVP.
*   Keep attribute lists initially focused on essential data.
*   Clearly define relationships, as these heavily influence data modeling in the next step.
*   Ensure terminology is consistent with Step 1 outputs.
*   The Logical Data Model is a crucial input for the `DatabaseAgent` in Step 3. 