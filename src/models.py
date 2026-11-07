from __future__ import annotations

# dataclass reduces boilerplate for model classes.
from dataclasses import dataclass, asdict

# These type hints make the models clearer and interview-friendly.
from typing import List, Dict, Any


# Customer represents the customer master data used by the proposal.
@dataclass
class Customer:
    # Unique customer identifier.
    customer_id: str
    # Company name shown in the proposal.
    company_name: str
    # Main contact person for the deal.
    contact_name: str
    # Contact email.
    email: str
    # Contact phone number.
    phone: str
    # Billing address used for commercial reference.
    billing_address: str
    # Industry used for pricing/discount rules.
    industry: str
    # Generic sales owner or account owner.
    account_owner: str


# Product represents product catalog data.
@dataclass
class Product:
    # Internal or public product ID.
    product_id: str
    # Human-readable SKU or code.
    sku: str
    # Product name used in quotations.
    name: str
    # Product description used for context.
    description: str
    # Feature list that could be used for richer prompts later.
    features: List[str]
    # Service category such as CRM, AI, Analytics, etc.
    service_category: str
    # Base price used for commercial calculations.
    base_price: float
    # Availability tag mapped to delivery rules.
    availability_tag: str


# ProposalLineItem captures the user's selected product and quantity.
@dataclass
class ProposalLineItem:
    # Product identifier selected by the user.
    product_id: str
    # Requested quantity.
    quantity: int


# ProposalRequest is the main input payload to the generation pipeline.
@dataclass
class ProposalRequest:
    # Customer chosen from the customer source.
    customer_id: str
    # Selected product lines.
    line_items: List[ProposalLineItem]
    # Free-text requirement summary typed by the user.
    customer_requirements: str
    # Commercial terms selected or entered by the user.
    special_terms: str
    # Requested delivery timeline chosen by the user.
    delivery_timeline_requested: str
    # Business objective selected by the user.
    objective: str
    # Optional additional discount percentage.
    special_discount_pct: float = 0.0
    # Optional notes to influence proposal tone.
    extra_comments: str = ''
    # Currency code for the quotation.
    currency: str = 'CAD'


# QuotationLine represents one output line in the final quotation table.
@dataclass
class QuotationLine:
    # SKU shown in the quotation.
    sku: str
    # Product name shown in the quotation.
    product_name: str
    # Final quantity.
    quantity: int
    # Final unit price after business rules choose the amount.
    unit_price: float
    # Final line total for the product row.
    line_total: float


# CommercialSummary holds the calculated money fields for the quote.
@dataclass
class CommercialSummary:
    # Total before discounts and taxes.
    subtotal: float
    # Combined discount percentage actually applied.
    discount_pct: float
    # Monetary discount amount.
    discount_amount: float
    # Amount after discount and before tax.
    taxed_subtotal: float
    # Tax percentage applied.
    tax_pct: float
    # Monetary tax amount.
    tax_amount: float
    # Final amount inclusive of tax.
    grand_total: float
    # Currency code.
    currency: str
    # Flag used for approval workflow ideas.
    requires_approval: bool


# ProposalDocument represents the final generated artifact.
@dataclass
class ProposalDocument:
    # Unique proposal identifier.
    proposal_id: str
    # Customer data section.
    customer: Customer
    # Final quotation lines.
    quotation_lines: List[QuotationLine]
    # Calculated commercial summary.
    commercial_summary: CommercialSummary
    # LLM-generated scope summary.
    scope_summary: str
    # LLM-generated assumptions.
    assumptions: List[str]
    # LLM-generated next steps.
    next_steps: List[str]
    # LLM-generated main proposal overview text.
    proposal_text: str
    # Final delivery statement after rules are applied.
    delivery_timeline_final: str
    # Generation status useful for future workflow states.
    status: str = 'generated'
    # Document version useful for versioning later.
    version: int = 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert the nested dataclass structure into a plain dictionary."""
        return asdict(self)
