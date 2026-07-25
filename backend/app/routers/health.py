from fastapi import APIRouter, HTTPException, status
from typing import List

from ..schemas import ArticleOut, MythFactOut
from ..utils import get_health_articles, get_myth_cards

router = APIRouter(prefix="/api/health", tags=["Health Library"])


@router.get("/articles", response_model=List[ArticleOut])
def list_articles():
    """Retrieve all health library articles."""
    return get_health_articles()


@router.get("/articles/{article_id}", response_model=ArticleOut)
def get_article(article_id: int):
    """Retrieve a single health article by ID."""
    articles = get_health_articles()
    article = next((a for a in articles if a["id"] == article_id), None)
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found."
        )
    return article


@router.get("/myths", response_model=List[MythFactOut])
def list_myths():
    """Retrieve all myth vs fact interactive cards."""
    return get_myth_cards()
