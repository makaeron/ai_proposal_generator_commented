from __future__ import annotations

# json is used to persist the structured document.
import json

# Path represents file paths in an OS-safe way.
from pathlib import Path

# Import the final document model to be stored.
from src.models import ProposalDocument


# ProposalStorage handles structured persistence.
class ProposalStorage:
    def __init__(self, output_dir: Path) -> None:
        # Save the output directory location.
        self.output_dir = output_dir

        # Ensure the folder exists before writing files.
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def save_json(self, document: ProposalDocument) -> Path:
        """Save the full proposal document as a formatted JSON file."""

        # Build the target file path using the proposal ID.
        path = self.output_dir / f'{document.proposal_id}.json'

        # Open the file for writing in UTF-8.
        with open(path, 'w', encoding='utf-8') as f:
            # Convert the document to a dictionary and write pretty JSON.
            json.dump(document.to_dict(), f, indent=2)

        # Return the saved path so the caller can print it.
        return path
