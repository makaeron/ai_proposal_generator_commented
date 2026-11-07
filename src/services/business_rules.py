from __future__ import annotations

# Type hints make the service easier to read and explain in interviews.
from typing import List, Tuple

# Import constants for discount approval threshold and fallback tax.
from src.config import APPROVAL_DISCOUNT_THRESHOLD, DEFAULT_TAX_PCT

# Import the data models used by this service.
from src.models import ProposalRequest, Customer, Product, QuotationLine, CommercialSummary


# BusinessRulesEngine keeps all deterministic calculations outside the LLM.
class BusinessRulesEngine:
    def build_commercials(
        self,
        request: ProposalRequest,
        customer: Customer,
        products_with_qty: List[Tuple[Product, int]],
        pricing_rules: dict,
        delivery_rules: dict,
    ) -> tuple[List[QuotationLine], CommercialSummary, str]:
        """Build quotation lines, money totals, and the final delivery message."""

        # Read the regional tax percentage for Ontario.
        # If not found, fall back to the default tax.
        regional_tax_pct = pricing_rules.get('regional_tax_pct', {}).get('CA-ON', DEFAULT_TAX_PCT)

        # Read any industry-based discount benefit.
        # If the customer's industry has no entry, use 0.
        tier_discount_pct = pricing_rules.get('industry_discount_pct', {}).get(customer.industry, 0.0)

        # Combine user-entered discount and rule-based industry discount.
        # Cap the total discount at 30% to avoid unrealistic values.
        combined_discount_pct = min(request.special_discount_pct + tier_discount_pct, 30.0)

        # This will collect the final display rows for the quotation.
        quotation_lines: List[QuotationLine] = []

        # Start subtotal at zero and build it line by line.
        subtotal = 0.0

        # Track the slowest product availability so the final timeline is realistic.
        max_delivery_days = 0

        # Process each selected product and quantity.
        for product, qty in products_with_qty:
            # Use the product base price as the unit price.
            unit_price = round(product.base_price, 2)

            # Calculate line total for this row.
            line_total = round(unit_price * qty, 2)

            # Add the line total to the overall subtotal.
            subtotal += line_total

            # Compare product availability against the current maximum timeline.
            max_delivery_days = max(max_delivery_days, delivery_rules.get(product.availability_tag, 15))

            # Append a display-ready quotation line.
            quotation_lines.append(
                QuotationLine(
                    sku=product.sku,
                    product_name=product.name,
                    quantity=qty,
                    unit_price=unit_price,
                    line_total=line_total,
                )
            )

        # Convert the discount percentage into a money value.
        discount_amount = round(subtotal * (combined_discount_pct / 100.0), 2)

        # Calculate the amount after discount but before tax.
        taxed_subtotal = round(subtotal - discount_amount, 2)

        # Calculate tax on the discounted subtotal.
        tax_amount = round(taxed_subtotal * (regional_tax_pct / 100.0), 2)

        # Calculate the final grand total.
        grand_total = round(taxed_subtotal + tax_amount, 2)

        # Package the calculated commercial values into a dedicated output model.
        summary = CommercialSummary(
            subtotal=round(subtotal, 2),
            discount_pct=round(combined_discount_pct, 2),
            discount_amount=discount_amount,
            taxed_subtotal=taxed_subtotal,
            tax_pct=regional_tax_pct,
            tax_amount=tax_amount,
            grand_total=grand_total,
            currency=request.currency,
            requires_approval=combined_discount_pct > APPROVAL_DISCOUNT_THRESHOLD,
        )

        # Convert the slowest product availability into a human-readable timeline.
        delivery_timeline_final = f'Estimated delivery / kickoff within {max_delivery_days} business days'

        # Return all deterministic outputs to the orchestration layer.
        return quotation_lines, summary, delivery_timeline_final
