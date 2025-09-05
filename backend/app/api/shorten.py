# backend/app/api/shorten.py
from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Request, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.session import get_db
from app.services import url_service
from app.services.rate_limit import rate_limit_or_429

router = APIRouter(prefix="/api", tags=["shortener"])


class CreateShortLinkRequest(BaseModel):
    url: str
    alias: Optional[str] = None
    expires_at: Optional[datetime] = None


class CreateShortLinkResponse(BaseModel):
    code: str
    short_url: str


class ResolveResponse(BaseModel):
    exists: bool
    expired: bool
    long_url: Optional[str] = None



@router.post("/shorten", response_model=CreateShortLinkResponse, status_code=status.HTTP_201_CREATED)
def create_short_link(
    payload: CreateShortLinkRequest,
    request: Request,
    _rl: None = Depends(rate_limit_or_429),  # per-IP limiter
    db: Session = Depends(get_db),
):
    try:
        code, _link = url_service.create_short_link(
            db,
            url=payload.url,
            alias=payload.alias,
            expires_at=payload.expires_at,
        )
    except url_service.InvalidURLError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except url_service.InvalidAliasError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except url_service.AliasTakenError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except url_service.RetryExhaustedError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))

    short_url = url_service.build_short_url(str(request.base_url), code)
    return CreateShortLinkResponse(code=code, short_url=short_url)


@router.get(
    "/resolve/{code}",
    response_model=ResolveResponse,
    response_model_exclude_none=True,  
)
def resolve_code(
    code: str = Path(..., min_length=3, max_length=32),
    db: Session = Depends(get_db),
):
    """
    Resolve metadata for a short code (no redirect).
    """
    data = url_service.resolve(db, code=code)
    return ResolveResponse(**data)
