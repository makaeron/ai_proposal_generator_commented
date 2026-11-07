from __future__ import annotations

# json is used for loading local mock files and parsing HTTP responses.
import json

# Path is used by the local JSON connector.
from pathlib import Path

# Type hints and Protocol help document the connector contract.
from typing import Dict, Any, List, Protocol

# urllib is used for lightweight public API calls without extra dependencies.
from urllib import request as urlrequest
from urllib.error import URLError, HTTPError

# Import data models returned by the connectors.
from src.models import Customer, Product
# DataConnector defines the methods expected by the generator service.
class DataConnector(Protocol):
    def get_customer(self, customer_id: str) -> Customer: ...
    def get_product(self, product_id: str) -> Product: ...
    def get_pricing_rules(self) -> Dict[str, Any]: ...
    def get_delivery_rules(self) -> Dict[str, Any]: ...
    def list_products(self) -> List[Product]: ...
    def list_customers(self) -> List[Customer]: ...

# JsonDataConnector acts like a mock API client backed by local JSON files.
class JsonDataConnector:
    """Mock API client backed by local JSON files."""

    def __init__(self, data_dir: Path) -> None:
        # Save the data folder location for later file reads.
        self.data_dir = data_dir

    def _load_json(self, filename: str) -> Dict[str, Any]:
        """Load a JSON file from the data directory and return a dictionary."""

        # Open the target file with UTF-8 encoding.
        with open(self.data_dir / filename, 'r', encoding='utf-8') as f:
            # Parse the JSON text into a Python object.
            return json.load(f)

    def get_customer(self, customer_id: str) -> Customer:
        """Return one customer by ID from local data."""

        # Load the full customer dictionary.
        data = self._load_json('customers.json')

        # Look up the requested customer directly.
        raw = data.get(customer_id)

        # If a numeric ID is used, fall back to the first record.
        # This helps when public-style IDs are passed while offline.
        if raw is None and customer_id.isdigit():
            raw = next(iter(data.values()))

        # Raise a clear error if nothing was found.
        if raw is None:
            raise KeyError(f'Unknown customer_id: {customer_id}')

        # Convert the dictionary into a typed Customer object.
        return Customer(**raw)

    def get_product(self, product_id: str) -> Product:
        """Return one product by ID from local data."""

        # Load the full product dictionary.
        data = self._load_json('products.json')

        # Look up the requested product directly.
        raw = data.get(product_id)

        # If a numeric ID is used, map it to a 1-based index in the local list.
        if raw is None and product_id.isdigit():
            items = list(data.values())
            index = max(0, min(len(items) - 1, int(product_id) - 1))
            raw = items[index]

        # Raise a clear error if the product does not exist.
        if raw is None:
            raise KeyError(f'Unknown product_id: {product_id}')

        # Convert the dictionary into a typed Product object.
        return Product(**raw)

    def get_pricing_rules(self) -> Dict[str, Any]:
        """Return deterministic pricing rules from local JSON."""
        return self._load_json('pricing_rules.json')

    def get_delivery_rules(self) -> Dict[str, Any]:
        """Return deterministic delivery rules from local JSON."""
        return self._load_json('delivery_rules.json')

    def list_products(self) -> List[Product]:
        """Return all available products as typed Product objects."""
        data = self._load_json('products.json')
        return [Product(**raw) for raw in data.values()]

    def list_customers(self) -> List[Customer]:
        """Return all available customers as typed Customer objects."""
        data = self._load_json('customers.json')
        return [Customer(**raw) for raw in data.values()]


# DummyJsonPublicConnector fetches generic data from a public API.
# If that fails, it falls back to the local JSON connector.
class DummyJsonPublicConnector:
    """Public API connector using DummyJSON for generic users and products.

    Falls back to local connector when public endpoints are unavailable.
    """

    def __init__(self, fallback: JsonDataConnector, base_url: str = 'https://dummyjson.com') -> None:
        # Save the local connector used when internet calls fail.
        self.fallback = fallback

        # Normalize the public API base URL by removing any trailing slash.
        self.base_url = base_url.rstrip('/')

    def _fetch_json(self, path: str) -> Dict[str, Any]:
        """Fetch JSON from the public API and return it as a dictionary."""

        # Build a simple GET request asking for JSON.
        req = urlrequest.Request(f"{self.base_url}/{path.lstrip('/')}" , headers={'Accept': 'application/json'})

        # Call the endpoint and decode the response body.
        with urlrequest.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode('utf-8'))

    def get_customer(self, customer_id: str) -> Customer:
        """Return a generic customer, using public API first and local fallback second."""
        try:
            # Support either raw numeric IDs or prefixed public IDs.
            public_id = int(customer_id.replace('PUB-CUST-', '')) if customer_id.startswith('PUB-CUST-') else int(customer_id)

            # Read one public user.
            raw = self._fetch_json(f'users/{public_id}')

            # Map the public user shape into our internal Customer model.
            return Customer(
                customer_id=f"PUB-CUST-{raw['id']}",
                company_name=raw.get('company', {}).get('name') or f"{raw['firstName']} {raw['lastName']} Consulting",
                contact_name=f"{raw['firstName']} {raw['lastName']}",
                email=raw.get('email', 'contact@example.com'),
                phone=raw.get('phone', 'N/A'),
                billing_address=f"{raw.get('address', {}).get('address', '')}, {raw.get('address', {}).get('city', '')}, {raw.get('address', {}).get('state', '')}",
                industry=raw.get('company', {}).get('department', 'General Business'),
                account_owner='Account Executive',
            )
        except (ValueError, KeyError, URLError, HTTPError, TimeoutError):
            # If anything goes wrong, return a local generic customer instead.
            return self.fallback.get_customer(customer_id)

    def get_product(self, product_id: str) -> Product:
        """Return a generic product, using public API first and local fallback second."""
        try:
            # Support either raw numeric IDs or prefixed public IDs.
            public_id = int(product_id.replace('PUB-PROD-', '')) if product_id.startswith('PUB-PROD-') else int(product_id)

            # Read one public product.
            raw = self._fetch_json(f'products/{public_id}')

            # Map the public product shape into our internal Product model.
            return Product(
                product_id=f"PUB-PROD-{raw['id']}",
                sku=f"SKU-{raw['id']:04d}",
                name=raw.get('title', 'Generic Product'),
                description=raw.get('description', 'Public API product'),
                features=[raw.get('category', 'general'), raw.get('brand', 'generic')],
                service_category=raw.get('category', 'Software'),
                base_price=float(raw.get('price', 0.0)),
                availability_tag='standard',
            )
        except (ValueError, KeyError, URLError, HTTPError, TimeoutError):
            # If anything goes wrong, return a local product instead.
            return self.fallback.get_product(product_id)

    def get_pricing_rules(self) -> Dict[str, Any]:
        """Pricing rules remain local because pricing should be deterministic."""
        return self.fallback.get_pricing_rules()

    def get_delivery_rules(self) -> Dict[str, Any]:
        """Delivery rules remain local because they are part of business logic."""
        return self.fallback.get_delivery_rules()

    def list_products(self) -> List[Product]:
        """List a few public products, or fall back to local products."""
        try:
            raw = self._fetch_json('products?limit=5')
            return [self.get_product(str(item['id'])) for item in raw.get('products', [])]
        except (URLError, HTTPError, TimeoutError, KeyError):
            return self.fallback.list_products()

    def list_customers(self) -> List[Customer]:
        """List a few public users, or fall back to local customers."""
        try:
            raw = self._fetch_json('users?limit=5')
            return [self.get_customer(str(item['id'])) for item in raw.get('users', [])]
        except (URLError, HTTPError, TimeoutError, KeyError):
            return self.fallback.list_customers()
