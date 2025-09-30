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
from app.db import session_scope
from app.models import Tenant


def generate_client_secret(length: int = 32) -> str:
    """Generate a secure random client secret."""
    return secrets.token_urlsafe(length)


def create_tenant(name: str, client_id: str) -> dict:
    """Create a new tenant with the given parameters."""
    settings = get_settings()

    # Generate secure client secret
    client_secret = generate_client_secret()

    # Create tenant in database
    with session_scope() as session:
        # Check if tenant with this oauth_client_id already exists
        existing = session.query(Tenant).filter_by(oauth_client_id=client_id).first()
        if existing:
            print(f"❌ Tenant with client_id '{client_id}' already exists!")
            print(f"   Tenant ID: {existing.id}")
            print(f"   Name: {existing.name}")
            return {
                "error": "Tenant already exists",
                "tenant_id": existing.id,
                "name": existing.name,
                "client_id": existing.oauth_client_id,
            }

        # Generate secure secrets for the tenant
        tenant_secret = secrets.token_urlsafe(32)
        webhook_secret = secrets.token_urlsafe(32)

        # Create new tenant
        tenant = Tenant(
            name=name,
            oauth_client_id=client_id,
            oauth_client_secret=client_secret,
            tenant_secret=tenant_secret,
            webhook_secret=webhook_secret,
            rate_limit_rps=10,
        )
        session.add(tenant)
        session.commit()
        session.refresh(tenant)

        return {
            "tenant_id": tenant.id,
            "name": tenant.name,
            "client_id": tenant.oauth_client_id,
            "client_secret": client_secret,
            "tenant_secret": tenant_secret,
            "webhook_secret": webhook_secret,
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
    args = parser.parse_args()

    print(f"Creating tenant: {args.name}")
    print(f"Client ID: {args.client_id}")
    print()

    result = create_tenant(args.name, args.client_id)

    if "error" in result:
        sys.exit(1)

    print("✅ Tenant created successfully!")
    print()
    print("=" * 60)
    print("IMPORTANT: Save these credentials securely!")
    print("=" * 60)
    print()
    print(f"Tenant ID:       {result['tenant_id']}")
    print(f"Name:            {result['name']}")
    print(f"Client ID:       {result['client_id']}")
    print(f"Client Secret:   {result['client_secret']}")
    print(f"Tenant Secret:   {result['tenant_secret']}")
    print(f"Webhook Secret:  {result['webhook_secret']}")
    print()
    print("=" * 60)
    print()
    print("Use these credentials to:")
    print("1. Login to dashboard: https://console.softmax.mn")
    print("2. Make API requests with OAuth2 authentication")
    print("3. Sign webhook deliveries")
    print()


if __name__ == "__main__":
    main()