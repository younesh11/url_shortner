from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse

from app.db.session import get_db
from app.db import repository as repo
from app.services import url_service


router = APIRouter(tags=["redirect"])

@router.get(
    "/{code}",
    include_in_schema=False,  
)
def redirect_code(
    code: str = Path(..., pattern=r"^[A-Za-z0-9_-]{3,32}$"),
    db: Session = Depends(get_db),
):
    
    if url_service.is_reserved_alias(code):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    link = url_service.lookup_active_for_redirect(db, code=code)
    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    
    try:
        repo.increment_click_count(db, code)
    except Exception:
        pass

    # 302 is conventional for shorteners; switch to 301 if you want permanence/caching
    return RedirectResponse(url=link.long_url, status_code=status.HTTP_302_FOUND)
