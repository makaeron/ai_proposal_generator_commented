from __future__ import annotations

# datetime is used to generate a unique proposal ID.
from datetime import datetime

# Import the input and output models.
from src.models import ProposalRequest, ProposalDocument

# Import the connector protocol used to fetch source data.
from src.services.connectors import DataConnector

# Import the validator layer.
from src.services.validator import ProposalValidator

# Import deterministic business rules.
from src.services.business_rules import BusinessRulesEngine

# Import the LLM provider abstraction.
from src.services.llm_provider import BaseLLMProvider


# ProposalGeneratorService orchestrates the full proposal pipeline.
class ProposalGeneratorService:
    def __init__(
        self,
        connector: DataConnector,
        validator: ProposalValidator,
        business_rules: BusinessRulesEngine,
        llm_provider: BaseLLMProvider,
    ) -> None:
        # Save injected dependencies so they can be swapped independently.
        self.connector = connector
        self.validator = validator
        self.business_rules = business_rules
        self.llm_provider = llm_provider

    def generate(self, request: ProposalRequest) -> ProposalDocument:
        """Run validation, data fetch, pricing, LLM generation, and document assembly."""

        # Step 1: validate the request before doing any expensive work.
        self.validator.validate(request)

        # Step 2: fetch customer master data from the connector.
        customer = self.connector.get_customer(request.customer_id)

        # Step 3: fetch each selected product and pair it with quantity.
        products_with_qty = [
            (self.connector.get_product(item.product_id), item.quantity)
            for item in request.line_items
        ]

        # Step 4: load deterministic pricing and delivery rules.
        pricing_rules = self.connector.get_pricing_rules()
        delivery_rules = self.connector.get_delivery_rules()

        # Step 5: calculate all commercial outputs outside the LLM.
        quotation_lines, commercial_summary, delivery_timeline_final = self.business_rules.build_commercials(
            request=request,
            customer=customer,
            products_with_qty=products_with_qty,
            pricing_rules=pricing_rules,
            delivery_rules=delivery_rules,
        )

        # Step 6: build a clean structured payload for the text-generation layer.
        payload = {
            'customer': customer.__dict__,
            'quotation_lines': [line.__dict__ for line in quotation_lines],
            'commercial_summary': commercial_summary.__dict__,
            'customer_requirements': request.customer_requirements,
            'special_terms': request.special_terms,
            'objective': request.objective,
            'delivery_timeline_requested': request.delivery_timeline_requested,
            'delivery_timeline_final': delivery_timeline_final,
            'extra_comments': request.extra_comments,
        }

        # Step 7: ask the provider to generate language sections.
        generated = self.llm_provider.generate_sections(payload)

        # Step 8: create a unique proposal identifier based on current timestamp.
        proposal_id = f"PROP-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

        # Step 9: assemble the final ProposalDocument object.
        return ProposalDocument(
            proposal_id=proposal_id,
            customer=customer,
            quotation_lines=quotation_lines,
            commercial_summary=commercial_summary,
            scope_summary=generated['scope_summary'],
            assumptions=generated['assumptions'],
            next_steps=generated['next_steps'],
            proposal_text=generated['proposal_text'],
            delivery_timeline_final=delivery_timeline_final,
        )
