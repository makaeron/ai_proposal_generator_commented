from __future__ import annotations

# json is used both for request bodies and for parsing model responses.
import json

# Type hints clarify the payload contract.
from typing import Dict, Any

# urllib lets us call the Ollama HTTP endpoint without extra packages.
from urllib import request as urlrequest
from urllib.error import URLError


# BaseLLMProvider defines the interface expected by the generator service.
class BaseLLMProvider:
    def generate_sections(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError


# MockLLMProvider is a deterministic fallback.
# It keeps the project runnable even when no model server exists.
class MockLLMProvider(BaseLLMProvider):
    """Deterministic fallback so the project runs even when Ollama is unavailable."""

    def generate_sections(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Generate stable proposal sections from templates instead of an actual LLM."""

        # Pull the customer block from the payload.
        customer = payload['customer']

        # Pull the commercial summary to reference totals and currency.
        commercial = payload['commercial_summary']

        # Build a comma-separated product list for readable business text.
        product_names = ', '.join(line['product_name'] for line in payload['quotation_lines'])

        # Build a compact scope summary.
        scope_summary = (
            f"This proposal addresses {customer['company_name']}'s requirement for {payload['objective'].lower()} "
            f'using the proposed solution set covering {product_names}.'
        )

        # Define standard assumptions used by the proposal.
        assumptions = [
            'Customer will confirm final requirements and sign-off points before kickoff.',
            'Commercials are based on the current quantities, product selection, and agreed scope.',
            'Additional scope, integration work, or change requests will be reviewed separately.',
        ]

        # Define standard next steps shown at the end of the proposal.
        next_steps = [
            'Review the scope summary and quotation details.',
            'Confirm commercials, delivery expectations, and terms.',
            'Approve the proposal to begin onboarding and execution planning.',
        ]

        # Build the main proposal paragraph.
        proposal_text = (
            f"Thank you for the opportunity to present this proposal for {customer['company_name']}. "
            f"Based on the business objective of {payload['objective']}, we recommend the proposed solution to improve operational consistency and quotation turnaround. "
            f"The total commercial value is {commercial['currency']} {commercial['grand_total']:.2f} inclusive of tax. "
            f'The response has been drafted in a business-friendly format so it can be reviewed internally and shared externally with minimal edits.'
        )

        # Return the exact structure expected by the generator service.
        return {
            'scope_summary': scope_summary,
            'assumptions': assumptions,
            'next_steps': next_steps,
            'proposal_text': proposal_text,
        }


# OllamaLLMProvider calls a local Ollama server for real generation.
class OllamaLLMProvider(BaseLLMProvider):
    def __init__(self, base_url: str, model: str) -> None:
        # Save endpoint and model name for future requests.
        self.base_url = base_url
        self.model = model

    def generate_sections(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Send the payload to Ollama and parse the expected JSON response."""

        # Convert the business payload into a text prompt.
        prompt = self._build_prompt(payload)

        # Build an HTTP POST request for Ollama.
        req = urlrequest.Request(
            self.base_url,
            data=json.dumps({'model': self.model, 'prompt': prompt, 'stream': False}).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST',
        )
        try:
            # Call Ollama and parse the top-level response body.
            with urlrequest.urlopen(req, timeout=45) as resp:
                body = json.loads(resp.read().decode('utf-8'))
        except URLError as exc:
            # Raise a cleaner runtime error if the server is unavailable.
            raise RuntimeError(f'Unable to reach Ollama: {exc}') from exc

        # Ollama returns generated text under the `response` key.
        raw = body.get('response', '')
        try:
            # We expect the generated text itself to be valid JSON.
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            # Tell the caller exactly what failed.
            raise RuntimeError('Ollama response was not valid JSON. Use MockLLMProvider or improve prompt.') from exc

    def _build_prompt(self, payload: Dict[str, Any]) -> str:
        """Build a strict prompt asking the model for structured JSON output."""
        return (
            'You are a business proposal assistant. Generate a valid JSON object with keys: '
            'scope_summary (string), assumptions (list of strings), next_steps (list of strings), proposal_text (string). '
            'Keep language professional, concise, generic, and client-friendly. Do not invent personal names. Input payload:\n'
            + json.dumps(payload, indent=2)
        )
