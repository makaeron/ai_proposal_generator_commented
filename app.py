from __future__ import annotations

# Import the built-in sys module so we can read command-line arguments
# such as --sample, --public, and --ollama.
import sys

# Import Path so we can build reliable file-system paths.
from pathlib import Path

# Resolve the absolute path of the project root directory.
# app.py sits at the root, so parent is the project folder itself.
ROOT = Path(__file__).resolve().parent

# Add the project root to Python's module search path if needed.
# This allows imports like `from src.config import ...` to work
# even when the file is run directly with `python app.py`.
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Import application-level configuration constants.
from src.config import DATA_DIR, OUTPUT_DIR, DEFAULT_OLLAMA_MODEL, DEFAULT_OLLAMA_URL

# Import request and line-item models used to build the proposal input.
from src.models import ProposalRequest, ProposalLineItem

# Import the local JSON connector and the public API connector.
from src.services.connectors import JsonDataConnector, DummyJsonPublicConnector

# Import the validator that checks request completeness and correctness.
from src.services.validator import ProposalValidator

# Import the business-rules engine that calculates prices, taxes, and timeline.
from src.services.business_rules import BusinessRulesEngine

# Import both LLM provider options.
# MockLLMProvider gives deterministic local output.
# OllamaLLMProvider calls a local Ollama endpoint.
from src.services.llm_provider import MockLLMProvider, OllamaLLMProvider

# Import the orchestration service that ties together validation,
# connectors, business rules, and LLM text generation.
from src.services.generator import ProposalGeneratorService

# Import storage/export helpers for JSON and human-readable outputs.
from src.services.storage import ProposalStorage
from src.services.exporter import ProposalExporter


# Menu options presented to the user for delivery timeline.
TIMELINE_OPTIONS = [
    'Within 2 weeks',
    'Within 4 weeks',
    'Within 6 weeks',
]

# Menu options presented to the user for commercial terms.
PAYMENT_TERM_OPTIONS = [
    'Net 15 payment terms. Proposal validity is 15 days.',
    'Net 30 payment terms. Proposal validity is 30 days.',
    '50% upfront and 50% upon delivery. Proposal validity is 30 days.',
]

# Menu options for the business objective behind the proposal.
OBJECTIVE_OPTIONS = [
    'Sales process improvement and faster quotation turnaround',
    'Customer engagement improvement and standardized proposal quality',
    'Operational efficiency and better proposal consistency across the sales team',
]

# Menu options for currency selection.
CURRENCY_OPTIONS = ['CAD', 'USD']


def ask(prompt: str, default: str = '') -> str:
    """Ask the user for console input and return the typed value.

    If the user presses Enter without typing anything, the default value is used.
    This keeps the demo fast while still allowing customization.
    """

    # Create a visible suffix only when a default exists.
    suffix = f' [{default}]' if default else ''

    # Display the prompt and strip leading/trailing spaces from the response.
    value = input(f'{prompt}{suffix}: ').strip()

    # Return the typed value if present; otherwise fall back to the default.
    return value or default


def choose_option(title: str, options: list[str], default_index: int = 1) -> str:
    """Display numbered options and return the selected option text."""

    # Print a heading so the user knows what category is being selected.
    print(f'\n{title}:')

    # Print each option with a 1-based index for easy selection.
    for idx, option in enumerate(options, start=1):
        print(f'  {idx}. {option}')

    # Keep asking until the user enters a valid number.
    while True:
        # Reuse the shared ask() helper and prefill a sensible default.
        raw = ask('Select option number', str(default_index))

        # Accept only digits that map to a real option position.
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return options[int(raw) - 1]

        # Tell the user what went wrong and loop again.
        print('Please enter a valid option number.')


def choose_customer(connector):
    """Display available customers and return the selected Customer object."""

    # Read customers from the active connector.
    # In local mode this comes from JSON.
    # In public mode this may come from DummyJSON with local fallback.
    customers = connector.list_customers()[:5]

    # Show a compact list to the user.
    print('\nAvailable customers:')
    for idx, customer in enumerate(customers, start=1):
        print(f'  {idx}. {customer.company_name} ({customer.contact_name})')

    # Keep asking until a valid option is selected.
    while True:
        raw = ask('Select customer number', '1')
        if raw.isdigit() and 1 <= int(raw) <= len(customers):
            return customers[int(raw) - 1]
        print('Please enter a valid customer number.')


def choose_products(connector) -> list[ProposalLineItem]:
    """Allow the user to select one or more products and quantities."""

    # Load product choices from the active connector.
    products = connector.list_products()[:5]

    # Print all visible products with a few useful business fields.
    print('\nAvailable products:')
    for idx, product in enumerate(products, start=1):
        print(f'  {idx}. {product.name} | {product.base_price} | {product.service_category}')

    # This list will collect ProposalLineItem objects chosen by the user.
    selected: list[ProposalLineItem] = []

    # Loop until the user explicitly finishes.
    while True:
        # If no product has been selected yet, default to 1.
        # Once at least one exists, default to 0 so the user can finish quickly.
        raw = ask('Select product number (or 0 to finish)', '1' if not selected else '0')

        # If the user enters 0, try to end the selection flow.
        if raw == '0':
            # At least one product is required.
            if selected:
                return selected
            print('Please add at least one product.')
            continue

        # Reject invalid non-numeric values or values outside the range.
        if not raw.isdigit() or not (1 <= int(raw) <= len(products)):
            print('Please enter a valid product number.')
            continue

        # Convert the chosen number into the actual Product object.
        product = products[int(raw) - 1]

        # Ask for quantity for the selected product.
        qty_raw = ask(f'Quantity for {product.name}', '1')

        # Validate the quantity.
        if not qty_raw.isdigit() or int(qty_raw) <= 0:
            print('Quantity must be a positive whole number.')
            continue

        # Check if the same product was already selected earlier.
        existing = next((item for item in selected if item.product_id == product.product_id), None)

        # If already selected, increase the quantity instead of duplicating the row.
        if existing:
            existing.quantity += int(qty_raw)
        else:
            # Otherwise create a fresh proposal line item.
            selected.append(ProposalLineItem(product_id=product.product_id, quantity=int(qty_raw)))


def build_interactive_request(connector) -> ProposalRequest:
    """Build a ProposalRequest from console selections and typed inputs."""

    # Let the user pick the customer first.
    customer = choose_customer(connector)

    # Let the user pick one or more products next.
    line_items = choose_products(connector)

    # Decide whether to ask only minimal information or also optional notes.
    mode = choose_option('Generation mode', ['Quick generate', 'Detailed generate'], default_index=1)

    # Build the request object that will move through validation,
    # business rules, and the LLM layer.
    request = ProposalRequest(
        customer_id=customer.customer_id,
        line_items=line_items,
        customer_requirements=ask(
            'Enter requirement summary',
            'Need a professional proposal with clear quotation, onboarding support, and reporting capabilities.',
        ),
        special_terms=choose_option('Payment terms', PAYMENT_TERM_OPTIONS, default_index=2),
        delivery_timeline_requested=choose_option('Delivery timeline', TIMELINE_OPTIONS, default_index=1),
        objective=choose_option('Business objective', OBJECTIVE_OPTIONS, default_index=1),
        special_discount_pct=float(ask('Discount percent', '5')),
        extra_comments='',
        currency=choose_option('Currency', CURRENCY_OPTIONS, default_index=1),
    )

    # Add notes differently depending on the selected generation mode.
    if mode == 'Detailed generate':
        request.extra_comments = ask(
            'Optional notes',
            'Keep the tone formal, customer-friendly, and outcome-oriented.',
        )
    else:
        request.extra_comments = 'Keep the tone formal and business-friendly.'

    # Return the fully assembled request.
    return request


def build_sample_request(public_mode: bool = False) -> ProposalRequest:
    """Return a ready-made request so the project can be tested without typing."""

    return ProposalRequest(
        customer_id='1' if public_mode else 'CUST-1001',
        line_items=[
            ProposalLineItem(product_id='1' if public_mode else 'PROD-CRM-001', quantity=1),
            ProposalLineItem(product_id='2' if public_mode else 'PROD-AI-002', quantity=1),
        ],
        customer_requirements='The customer wants a proposal for improving sales operations, faster follow-up handling, and standardizing client-facing proposal generation.',
        special_terms='Net 30 payment terms. Proposal validity is 30 days.',
        delivery_timeline_requested='Within 2 weeks',
        objective='Sales process improvement and faster quotation turnaround',
        special_discount_pct=5.0,
        extra_comments='Keep the tone formal and business-friendly.',
        currency='CAD',
    )


def main() -> None:
    """Entry point for the command-line application."""

    # Convert CLI arguments into a set for quick flag lookups.
    args = set(sys.argv[1:])

    # Decide which LLM provider to use.
    provider_name = 'ollama' if '--ollama' in args else 'mock'

    # Decide whether to try public API mode.
    public_mode = '--public' in args

    # Decide whether to bypass interactive input and use a prebuilt sample.
    sample_mode = '--sample' in args

    # Local JSON connector always exists and also serves as fallback.
    fallback_connector = JsonDataConnector(DATA_DIR)

    # In public mode, use the public connector with local fallback.
    # Otherwise use the local JSON connector directly.
    connector = DummyJsonPublicConnector(fallback_connector) if public_mode else fallback_connector

    # Instantiate the validator layer.
    validator = ProposalValidator()

    # Instantiate the business rules layer.
    rules = BusinessRulesEngine()

    # Choose the LLM provider implementation.
    llm_provider = (
        OllamaLLMProvider(DEFAULT_OLLAMA_URL, DEFAULT_OLLAMA_MODEL)
        if provider_name == 'ollama'
        else MockLLMProvider()
    )

    # Build the orchestration service using dependency injection.
    service = ProposalGeneratorService(connector, validator, rules, llm_provider)

    # Create storage/export helpers for saving outputs.
    storage = ProposalStorage(OUTPUT_DIR)
    exporter = ProposalExporter(OUTPUT_DIR)

    # Choose between sample request mode and fully interactive mode.
    request = build_sample_request(public_mode=public_mode) if sample_mode else build_interactive_request(connector)

    # Generate the final proposal document.
    document = service.generate(request)

    # Save the structured JSON copy.
    json_path = storage.save_json(document)

    # Save a human-readable text export.
    txt_path = exporter.export_text(document)

    # Save an HTML export suitable for browser viewing or later styling.
    html_path = exporter.export_html(document)

    # Print summary information for the user.
    print('\nProposal generated successfully')
    print(f'JSON: {json_path}')
    print(f'TXT : {txt_path}')
    print(f'HTML: {html_path}')
    print(f'Proposal ID: {document.proposal_id}')


# Run the application only when this file is executed directly.
if __name__ == '__main__':
    main()
