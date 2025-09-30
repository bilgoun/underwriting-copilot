#!/usr/bin/env python3
"""
Script to create OAuth2 tenants for the underwriting API dashboard.
"""
import argparse
import secrets
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import get_settings
from app.database import get_sync_session
from app.models import Tenant


def generate_client_secret(length: int = 32) -> str:
    """Generate a secure random client secret."""
    return secrets.token_urlsafe(length)


def create_tenant(name: str, client_id: str, scope: str) -> dict:
    """Create a new tenant with the given parameters."""
    settings = get_settings()

    # Generate secure client secret
    client_secret = generate_client_secret()

    # Create tenant in database
    with get_sync_session() as session:
        # Check if tenant with this client_id already exists
        existing = session.query(Tenant).filter_by(client_id=client_id).first()
        if existing:
            print(f"❌ Tenant with client_id '{client_id}' already exists!")
            print(f"   Tenant ID: {existing.id}")
            print(f"   Name: {existing.name}")
            print(f"   Scope: {existing.scope}")
            return {
                "error": "Tenant already exists",
                "tenant_id": existing.id,
                "name": existing.name,
                "client_id": existing.client_id,
                "scope": existing.scope,
            }

        # Create new tenant
        tenant = Tenant(
            name=name,
            client_id=client_id,
            client_secret=client_secret,
            scope=scope,
        )
        session.add(tenant)
        session.commit()
        session.refresh(tenant)

        return {
            "tenant_id": tenant.id,
            "name": tenant.name,
            "client_id": tenant.client_id,
            "client_secret": client_secret,
            "scope": tenant.scope,
        }


def main():
    parser = argparse.ArgumentParser(
        description="Create OAuth2 tenant for the underwriting API dashboard"
    )
    parser.add_argument(
        "--name",
        required=True,
        help="Display name for the tenant (e.g., 'Softmax Admin Console')",
    )
    parser.add_argument(
        "--client-id",
        required=True,
        help="Unique client ID (e.g., 'admin_prod', 'bank_xyz')",
    )
    parser.add_argument(
        "--scope",
        default="dashboard:read",
        help="OAuth2 scope (e.g., 'dashboard:admin', 'dashboard:read')",
    )

    args = parser.parse_args()

    print(f"Creating tenant: {args.name}")
    print(f"Client ID: {args.client_id}")
    print(f"Scope: {args.scope}")
    print()

    result = create_tenant(args.name, args.client_id, args.scope)

    if "error" in result:
        sys.exit(1)

    print("✅ Tenant created successfully!")
    print()
    print("=" * 60)
    print("IMPORTANT: Save these credentials securely!")
    print("=" * 60)
    print()
    print(f"Tenant ID:      {result['tenant_id']}")
    print(f"Name:           {result['name']}")
    print(f"Client ID:      {result['client_id']}")
    print(f"Client Secret:  {result['client_secret']}")
    print(f"Scope:          {result['scope']}")
    print()
    print("=" * 60)
    print()
    print("Login to the dashboard at: https://console.softmax.mn")
    print()


if __name__ == "__main__":
    main()