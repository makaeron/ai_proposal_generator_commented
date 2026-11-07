# AI Proposal / Quotation Generator - Architecture and Interview Guide

## 1. Architecture flow

User Input / Menu Selection  
→ Connector Layer  
→ Validation Layer  
→ Business Rules Layer  
→ LLM Generation Layer  
→ Proposal Document Assembly  
→ Storage + Export Layer

## 2. What each layer does

### User Input Layer
Captures what the user selects or types:
- customer
- products and quantities
- requirement summary
- payment terms
- delivery timeline
- business objective
- discount percent
- optional notes

### Connector Layer
Fetches source data.
- `JsonDataConnector`: local mock API using JSON files
- `DummyJsonPublicConnector`: public API first, local fallback second

### Validation Layer
Checks that the request is usable before processing.
Examples:
- customer exists
- at least one product is selected
- quantity is positive
- discount is not negative
- requirement summary is not empty

### Business Rules Layer
Handles deterministic logic that should **not** be left to the LLM.
Examples:
- product line totals
- subtotal
- discount amount
- tax amount
- grand total
- delivery timeline based on availability
- approval flag for large discounts

### LLM Generation Layer
Creates business language only.
It generates:
- proposal overview
- scope summary
- assumptions
- next steps

Important interview point:
**The LLM writes the wording, but the system calculates the money.**

### Proposal Assembly Layer
Packages all deterministic values and generated text into a `ProposalDocument` object.

### Storage + Export Layer
Stores the result in multiple formats:
- JSON for structured system storage
- TXT for easy reading
- HTML for browser-friendly presentation

## 3. Complete data pipeline

### Step 1: User starts the app
The user runs `python app.py`.

### Step 2: User selects menu options
The user chooses:
- one customer
- one or more products
- delivery option
- payment term
- objective
- optional notes

The only real free-text business field is the requirement summary.
 
### Step 3: ProposalRequest is created
The input is packaged into a `ProposalRequest` dataclass.

### Step 4: Request is validated
`ProposalValidator` checks whether required fields and quantities are valid.

### Step 5: Source data is fetched
The connector reads:
- customer data
- product data
- pricing rules
- delivery rules

### Step 6: Deterministic business calculations happen
`BusinessRulesEngine` calculates:
- quotation lines
- subtotal
- discounts
- taxed subtotal
- tax
- grand total
- final delivery timeline
- approval flag

### Step 7: Structured payload is built for the LLM
The app prepares a structured payload containing:
- customer block
- quotation lines
- money summary
- requirements
- selected terms
- objective
- notes

### Step 8: Text generation happens
The LLM provider returns:
- scope summary
- assumptions
- next steps
- proposal text

### Step 9: Final ProposalDocument is assembled
All structured and generated pieces are combined into one final object.

### Step 10: Output is saved
The project writes:
- `.json`
- `.txt`
- `.html`

## 4. Why the modular design is good

- Easier to test each part independently
- Easier to replace local JSON with real APIs later
- Easier to replace MockLLM with Ollama or another model
- Easier to debug because pricing logic is separate from generated text
- Cleaner explanation in interviews

## 5. Strong interview talk points

### Project summary
"This project is an AI-assisted proposal and quotation generator for sales workflows. It collects structured deal inputs, fetches customer and product data, applies deterministic pricing and delivery rules, then uses an LLM layer to generate professional proposal language such as scope summary, assumptions, and next steps."

### Why not let the LLM generate everything?
"I intentionally separated deterministic business logic from LLM generation. Pricing, tax, discounts, and delivery calculations are rule-based and must remain reliable. The LLM is used only for language generation and presentation-quality sections."

### Why modular files?
"I split the solution by responsibility: connectors for data access, validator for input checks, business rules for commercials, LLM provider for generation, generator service for orchestration, and storage/export for outputs. That makes the code maintainable and easier to extend."

### How can this scale later?
"The connector layer can be switched from mock JSON to real CRM, product, pricing, or ERP APIs. The LLM provider can be replaced from mock mode to Ollama, LangChain orchestration, or cloud-hosted models. The output layer can later add PDF and DOCX generation."

### Where is AI actually used?
"AI is used in the proposal authoring layer. After the structured commercial payload is finalized, the model generates the proposal overview, scope summary, assumptions, and next steps in a client-friendly format."

### How is hallucination controlled?
"By minimizing what the model is allowed to invent. We pass structured factual data into the provider and only ask it to write language sections. We do not ask it to invent pricing, totals, or customer master data."

### Why use a mock LLM provider?
"It allows the project to remain runnable and testable even when the actual model server is not available. That is helpful for demos, development, and CI-style testing."

### What is the role of public API mode?
"It demonstrates how the architecture can consume external data sources dynamically. The public connector fetches generic customer and product data, but still falls back to local data for resilience."

## 6. Quick explanation of each file

- `app.py` → command-line entry point and user interaction
- `src/config.py` → global constants and paths
- `src/models.py` → dataclasses for request, source data, and final output
- `src/services/connectors.py` → source data access layer
- `src/services/validator.py` → request validation rules
- `src/services/business_rules.py` → pricing, discount, tax, approval, timeline logic
- `src/services/llm_provider.py` → mock or Ollama generation
- `src/services/generator.py` → full orchestration pipeline
- `src/services/storage.py` → JSON persistence
- `src/services/exporter.py` → TXT and HTML exports

## 7. Best 90-second interview explanation

"The project starts with a menu-driven input flow where the user selects a customer, products, delivery timeline, payment terms, and business objective, and types a short requirement summary. That input is wrapped into a ProposalRequest object and validated. Then the connector layer fetches customer and product data from either local JSON or a public API with fallback. After that, the business-rules engine calculates the quotation lines, subtotal, discount, tax, final total, and delivery timeline. Only after the factual data is finalized do I pass a structured payload into the LLM layer. The model generates proposal text, assumptions, and next steps, while all commercial math stays deterministic. Finally, the system assembles a ProposalDocument and exports it as JSON, TXT, and HTML."
