from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..config import get_settings
from ..db import get_session, get_tenant_by_client_credentials
from ..schemas import OAuthTokenRequest, OAuthTokenResponse
from ..security import issue_access_token

router = APIRouter(tags=["auth"])


@router.post("/oauth/token", response_model=OAuthTokenResponse)
async def token_endpoint(
    request: OAuthTokenRequest,
    session: Session = Depends(get_session),
) -> OAuthTokenResponse:
    if request.grant_type != "client_credentials":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported grant type")

    scope = request.scope or "underwrite:create underwrite:read"
    scopes = scope.split()

    tenant = get_tenant_by_client_credentials(session, request.client_id, request.client_secret)
    if tenant is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = issue_access_token(tenant, scopes)
    settings = get_settings()
    return OAuthTokenResponse(
        access_token=token,
        scope=" ".join(scopes),
        expires_in=settings.oauth2_token_ttl_seconds,
    )
