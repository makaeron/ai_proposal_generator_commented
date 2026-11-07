from __future__ import annotations

# Path is used to create output file paths.
from pathlib import Path

# Import the proposal document model.
from src.models import ProposalDocument


# ProposalExporter creates user-friendly output files.
class ProposalExporter:
    def __init__(self, output_dir: Path) -> None:
        # Save the output directory location.
        self.output_dir = output_dir

        # Ensure the folder exists before writing files.
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export_text(self, document: ProposalDocument) -> Path:
        """Export the proposal as a plain-text business document."""

        # Build the target text file path.
        path = self.output_dir / f'{document.proposal_id}.txt'

        # Write the rendered text content to disk.
        with open(path, 'w', encoding='utf-8') as f:
            f.write(self._render_text(document))

        # Return the saved file path.
        return path

    def export_html(self, document: ProposalDocument) -> Path:
        """Export the proposal as a simple styled HTML file."""

        # Build the target HTML file path.
        path = self.output_dir / f'{document.proposal_id}.html'

        # Write the rendered HTML content to disk.
        with open(path, 'w', encoding='utf-8') as f:
            f.write(self._render_html(document))

        # Return the saved file path.
        return path

    def _render_text(self, document: ProposalDocument) -> str:
        """Create a readable plain-text representation of the proposal."""

        # Start with header lines and core proposal metadata.
        lines = [
            f'Proposal ID: {document.proposal_id}',
            f'Customer: {document.customer.company_name}',
            f'Contact: {document.customer.contact_name}',
            '',
            'PROPOSAL OVERVIEW',
            document.proposal_text,
            '',
            'SCOPE SUMMARY',
            document.scope_summary,
            '',
            'QUOTATION',
        ]

        # Add one plain-text line for each quotation row.
        for line in document.quotation_lines:
            lines.append(
                f'- {line.product_name} ({line.sku}) | Qty: {line.quantity} | Unit: {document.commercial_summary.currency} {line.unit_price:.2f} | Line Total: {document.commercial_summary.currency} {line.line_total:.2f}'
            )

        # Grab the commercial summary into a short variable for readability.
        cs = document.commercial_summary

        # Append totals, approval flag, timeline, assumptions, and next steps.
        lines.extend([
            '',
            f'Subtotal: {cs.currency} {cs.subtotal:.2f}',
            f'Discount ({cs.discount_pct}%): -{cs.currency} {cs.discount_amount:.2f}',
            f'Tax ({cs.tax_pct}%): {cs.currency} {cs.tax_amount:.2f}',
            f'Grand Total: {cs.currency} {cs.grand_total:.2f}',
            f"Approval Required: {'Yes' if cs.requires_approval else 'No'}",
            '',
            'DELIVERY TIMELINE',
            document.delivery_timeline_final,
            '',
            'ASSUMPTIONS',
        ])

        # Add assumptions as bullet-like lines.
        lines.extend([f'- {item}' for item in document.assumptions])

        # Add section header for next steps.
        lines.extend(['', 'NEXT STEPS'])

        # Add next steps as bullet-like lines.
        lines.extend([f'- {item}' for item in document.next_steps])

        # Join all text lines with newline characters.
        return '\n'.join(lines)

    def _render_html(self, document: ProposalDocument) -> str:
        """Create a simple browser-viewable HTML representation of the proposal."""

        # Build all quotation table rows as HTML strings.
        rows = ''.join(
            f'<tr><td>{line.product_name}</td><td>{line.sku}</td><td>{line.quantity}</td><td>{document.commercial_summary.currency} {line.unit_price:.2f}</td><td>{document.commercial_summary.currency} {line.line_total:.2f}</td></tr>'
            for line in document.quotation_lines
        )

        # Build assumption list items.
        assumptions = ''.join(f'<li>{item}</li>' for item in document.assumptions)

        # Build next-step list items.
        next_steps = ''.join(f'<li>{item}</li>' for item in document.next_steps)

        # Short alias for commercial summary.
        cs = document.commercial_summary

        # Return the final HTML document as one f-string.
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>{document.proposal_id}</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 32px; color: #222; }}
    h1, h2 {{ color: #123b73; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 12px; }}
    th, td {{ border: 1px solid #ccc; padding: 8px; text-align: left; }}
    th {{ background: #eef4ff; }}
    .box {{ padding: 12px; background: #f7f9fc; border: 1px solid #dbe3f1; margin: 12px 0; }}
  </style>
</head>
<body>
  <h1>Proposal / Quotation</h1>
  <div class="box">
    <strong>Proposal ID:</strong> {document.proposal_id}<br/>
    <strong>Customer:</strong> {document.customer.company_name}<br/>
    <strong>Contact:</strong> {document.customer.contact_name}<br/>
    <strong>Email:</strong> {document.customer.email}
  </div>
  <h2>Proposal Overview</h2>
  <p>{document.proposal_text}</p>
  <h2>Scope Summary</h2>
  <p>{document.scope_summary}</p>
  <h2>Quotation</h2>
  <table>
    <thead><tr><th>Product</th><th>SKU</th><th>Qty</th><th>Unit Price</th><th>Line Total</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
  <div class="box">
    <strong>Subtotal:</strong> {cs.currency} {cs.subtotal:.2f}<br/>
    <strong>Discount ({cs.discount_pct}%):</strong> -{cs.currency} {cs.discount_amount:.2f}<br/>
    <strong>Tax ({cs.tax_pct}%):</strong> {cs.currency} {cs.tax_amount:.2f}<br/>
    <strong>Grand Total:</strong> {cs.currency} {cs.grand_total:.2f}<br/>
    <strong>Approval Required:</strong> {'Yes' if cs.requires_approval else 'No'}
  </div>
  <h2>Delivery Timeline</h2>
  <p>{document.delivery_timeline_final}</p>
  <h2>Assumptions</h2>
  <ul>{assumptions}</ul>
  <h2>Next Steps</h2>
  <ul>{next_steps}</ul>
</body>
</html>
"""
