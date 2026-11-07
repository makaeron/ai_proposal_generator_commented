from __future__ import annotations

# Import the request model that will be validated.
from src.models import ProposalRequest


# Custom validation error makes failures easier to understand.
class ValidationError(Exception):
    pass


# Validator keeps input-quality checks separate from business logic.
class ProposalValidator:
    def validate(self, request: ProposalRequest) -> None:
        """Raise ValidationError when the request is incomplete or invalid."""

        # customer_id must exist and must not be blank.
        if not request.customer_id.strip():
            raise ValidationError('customer_id is required.')

        # customer_requirements is the key human-entered business input.
        if not request.customer_requirements.strip():
            raise ValidationError('customer_requirements is required.')

        # objective is used in both business framing and generated text.
        if not request.objective.strip():
            raise ValidationError('objective is required.')

        # At least one product line is required to build a quotation.
        if not request.line_items:
            raise ValidationError('At least one product line item is required.')

        # Discount cannot be negative.
        if request.special_discount_pct < 0:
            raise ValidationError('special_discount_pct cannot be negative.')

        # Every selected line item must have a positive quantity.
        for item in request.line_items:
            if item.quantity <= 0:
                raise ValidationError(f'Quantity must be positive for product {item.product_id}.')
