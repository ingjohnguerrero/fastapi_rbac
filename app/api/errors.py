"""Stable public error bodies (no existence leak)."""

from fastapi import HTTPException, status

DETAIL_UNAUTHORIZED = "Unauthorized"
DETAIL_FORBIDDEN = "Forbidden"
DETAIL_NOT_FOUND = "Not found"
DETAIL_CONFLICT = "Conflict"


def unauthorized() -> None:
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=DETAIL_UNAUTHORIZED)


def forbidden() -> None:
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=DETAIL_FORBIDDEN)


def not_found() -> None:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=DETAIL_NOT_FOUND)


def conflict() -> None:
    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=DETAIL_CONFLICT)
