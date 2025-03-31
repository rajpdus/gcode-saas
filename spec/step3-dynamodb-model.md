# Agent Plan: Step 3 - Define DynamoDB Data Model & Access Patterns

## 1. Goal

To design a specific, optimized AWS DynamoDB data model based on the logical model (entities, attributes, relationships) and Information Architecture defined in Step 2. This requires identifying and prioritizing the primary data access patterns.

## 2. Input

*   Logical Data Model (Entities, Attributes, Relationships from Step 2)
*   Basic Information Architecture Outline (from Step 2)
*   High-Level Core Objectives/Features (from Step 1, for context on usage)

## 3. Primary Agent(s) Involved

*   **`OrchestratorAgent`**: Manages the process, facilitates communication.
*   **`DatabaseAgent`**: Primary agent responsible for DynamoDB modeling and CloudFormation generation.
*   **`ArchitectureAgent`**: May provide oversight or clarification on access patterns based on the overall design.

## 4. Process / Workflow

1.  **Input Transfer:** `OrchestratorAgent` provides the Logical Data Model and IA outline to `DatabaseAgent` (and potentially `ArchitectureAgent` for context).
2.  **Access Pattern Identification:** `DatabaseAgent` (potentially guided by `ArchitectureAgent` or user clarification via `OrchestratorAgent`) analyzes the inputs to identify the most critical **Read/Write Access Patterns**. Examples:
    *   *Read:* Get user by ID, Get all orders for a specific user (sorted by date), Get product by SKU.
    *   *Write:* Create user, Update product inventory, Add item to order.
    *   **Complex Search Check:** The agent specifically looks for patterns requiring fuzzy text search, complex filtering across multiple fields, aggregations, or geospatial queries that are inefficient or impossible with DynamoDB alone (e.g., "Search documents by keyword", "Find products matching partial description and price range").
3.  **Table Design Strategy:** Based on relationships and access patterns, `DatabaseAgent` decides on the DynamoDB table strategy:
    *   Single-table design (preferred for related entities, using overloaded keys and indexes).
    *   Multi-table design (simpler for unrelated entities or very distinct access patterns).
    *   (Constraint: The system is opinionated towards single-table design where feasible for serverless benefits, but `DatabaseAgent` can choose multi-table if justified).
4.  **Key & Index Design:** `DatabaseAgent` defines:
    *   **Primary Keys (PK, SK):** Designs the Partition Key (PK) and Sort Key (SK) structure to support the most frequent access patterns efficiently. Often involves composite keys or overloaded keys/attributes.
    *   **Secondary Indexes (GSIs, LSIs):** Defines Global Secondary Indexes (GSIs) or Local Secondary Indexes (LSIs) to support alternative access patterns that aren't covered efficiently by the primary key.
5.  **Attribute Mapping:** Maps the logical attributes from Step 2 entities to specific attributes within the DynamoDB item structure, including data types.
6.  **CloudFormation Generation:** `DatabaseAgent` generates the CloudFormation YAML snippets for:
    *   The DynamoDB table(s) with defined keys, indexes, and capacity mode (default: On-Demand).
    *   Associated IAM Policy snippets granting specific CRUD permissions (e.g., `dynamodb:GetItem`, `dynamodb:PutItem`, `dynamodb:Query`, `dynamodb:UpdateItem`) scoped to the generated table(s). These snippets will be used by `InfrastructureAgent` later.
7.  **Data Access Pattern Examples:** `DatabaseAgent` generates basic Python code snippets illustrating how to perform the key identified access patterns using `boto3` against the designed table structure (e.g., `query` operation examples, `put_item` structure). **If complex search patterns were identified, notes are added indicating these patterns require OpenSearch.**
8.  **Flagging OpenSearch Need:** If the Complex Search Check (Step 2) identified patterns unsuitable for DynamoDB, the `DatabaseAgent` flags this requirement explicitly in its output.
9.  **Validation:** `OrchestratorAgent` performs basic checks (e.g., are all core entities represented? Do indexes support key access patterns? Was OpenSearch flagged if complex search exists?).

## 5. Output

*   **Physical DynamoDB Data Model:**
    *   Table name(s).
    *   Primary Key (PK, SK) structure definition for each table.
    *   GSI/LSI definitions (key structure, projections).
    *   Example item structures for each entity type within the table(s).
*   **CloudFormation Snippets:** YAML definitions for DynamoDB Table resource(s) and associated IAM Policy statement(s).
*   **Data Access Pattern Code Examples:** Python (`boto3`) snippets for key CRUD operations (with notes if OpenSearch is needed for some patterns).
*   **OpenSearch Requirement Flag:** A boolean flag or note indicating if subsequent steps need to incorporate OpenSearch integration.

## 6. Best Practices / Constraints Enforcement

*   **Access Pattern Driven Design:** The model MUST be optimized for the identified primary access patterns.
*   **DynamoDB Best Practices:** Adhere to DynamoDB principles (avoid scans, choose appropriate keys/indexes, consider item size limits).
*   **Single-Table Preference:** Favor single-table design for related data unless clearly disadvantageous.
*   **Least Privilege (IAM):** Generated IAM policy snippets MUST grant minimal required permissions.
*   **Clarity:** The model and access patterns should be clearly documented in the output.
*   **Constraint:** Only DynamoDB is designed in detail in this step. If the **OpenSearch Requirement Flag** is set, the design and integration of OpenSearch itself is deferred to Steps 5 and 6. 