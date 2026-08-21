from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

from ..database import get_db
from ..models import User, CommunityPost, CommunityComment
from .auth import get_current_user

router = APIRouter(prefix="/api/community", tags=["community"])


class PostCreateSchema(BaseModel):
    title: str
    content: str
    category: str = "General Q&A"
    author_name: Optional[str] = "Anonymous Member"


class PostResponseSchema(BaseModel):
    id: int
    user_id: int
    author_name: str
    category: str
    title: str
    content: str
    likes_count: int
    comments_count: int = 0
    created_at: str

    class Config:
        from_attributes = True

class CommentCreateSchema(BaseModel):
    content: str
    author_name: Optional[str] = "Anonymous Member"

class CommentResponseSchema(BaseModel):
    id: int
    post_id: int
    user_id: int
    author_name: str
    content: str
    created_at: str

    class Config:
        from_attributes = True

DEFAULT_POSTS = [
    {
        "id": 1,
        "user_id": 1,
        "author_name": "Ananya S.",
        "category": "PCOS Support",
        "title": "Low-GI Breakfast Ideas for PCOS Energy",
        "content": "Switching from sugary cereals to spinach egg scrambles with avocado has completely transformed my morning energy slumps! What are your favorite go-to low GI meals?",
        "likes_count": 24,
        "created_at": "2026-08-12T10:30:00"
    },
    {
        "id": 2,
        "user_id": 2,
        "author_name": "Meera R.",
        "category": "Fitness & Nutrition",
        "title": "Luteal Phase Workout Tips: Gentle Strength vs HIIT",
        "content": "I used to force myself to do heavy HIIT right before my period and feel exhausted. Switching to restorative yoga and light weight training in my luteal phase changed everything!",
        "likes_count": 18,
        "created_at": "2026-08-13T14:15:00"
    },
    {
        "id": 3,
        "user_id": 3,
        "author_name": "Priya M.",
        "category": "Mindfulness",
        "title": "Vera's 4-7-8 Breathing Technique Saved My Workday",
        "content": "Whenever cramp discomfort or meeting stress kicks in, 5 minutes of guided 4-7-8 breathing slows down my racing pulse. Highly recommend trying the built-in timer under Wellness!",
        "likes_count": 31,
        "created_at": "2026-08-14T09:00:00"
    }
]


@router.get("/posts")
def get_community_posts(category: Optional[str] = None, db: Session = Depends(get_db)):
    """Fetch community posts with optional category filter."""
    posts = db.query(CommunityPost).order_by(CommunityPost.created_at.desc()).all()
    
    if not posts:
        # Seed default initial posts into database if empty
        for p_data in DEFAULT_POSTS:
            new_post = CommunityPost(
                user_id=p_data["user_id"],
                author_name=p_data["author_name"],
                category=p_data["category"],
                title=p_data["title"],
                content=p_data["content"],
                likes_count=p_data["likes_count"]
            )
            db.add(new_post)
        db.commit()
        posts = db.query(CommunityPost).order_by(CommunityPost.created_at.desc()).all()

    if category and category != "All":
        posts = [p for p in posts if p.category.lower() == category.lower()]

    result = []
    for p in posts:
        result.append({
            "id": p.id,
            "user_id": p.user_id,
            "author_name": p.author_name or "Anonymous Member",
            "category": p.category,
            "title": p.title,
            "content": p.content,
            "likes_count": p.likes_count,
            "comments_count": len(p.comments) if hasattr(p, 'comments') else 0,
            "created_at": p.created_at.isoformat() if p.created_at else datetime.utcnow().isoformat()
        })
    return result


@router.post("/posts")
def create_community_post(
    post_data: PostCreateSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new community discussion post."""
    author = post_data.author_name
    if not author or author == "Anonymous Member":
        author = current_user.email.split("@")[0].capitalize() if current_user and current_user.email else "Anonymous Member"

    new_post = CommunityPost(
        user_id=current_user.id if current_user else 1,
        author_name=author,
        category=post_data.category or "General Q&A",
        title=post_data.title,
        content=post_data.content,
        likes_count=0
    )
    db.add(new_post)
    db.commit()
    db.refresh(new_post)

    return {
        "id": new_post.id,
        "user_id": new_post.user_id,
        "author_name": new_post.author_name,
        "category": new_post.category,
        "title": new_post.title,
        "content": new_post.content,
        "likes_count": new_post.likes_count,
        "created_at": new_post.created_at.isoformat()
    }


@router.post("/posts/{post_id}/like")
def like_community_post(post_id: int, db: Session = Depends(get_db)):
    """Increment likes on a community post."""
    post = db.query(CommunityPost).filter(CommunityPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    post.likes_count += 1
    db.commit()
    return {"id": post.id, "likes_count": post.likes_count}


@router.post("/posts/{post_id}/comments", response_model=CommentResponseSchema)
def create_comment(
    post_id: int,
    comment_data: CommentCreateSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a comment to a community post."""
    post = db.query(CommunityPost).filter(CommunityPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
        
    author = comment_data.author_name
    if not author or author == "Anonymous Member":
        author = current_user.email.split("@")[0].capitalize() if current_user and current_user.email else "Anonymous Member"

    new_comment = CommunityComment(
        post_id=post.id,
        user_id=current_user.id if current_user else 1,
        author_name=author,
        content=comment_data.content
    )
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)
    
    return {
        "id": new_comment.id,
        "post_id": new_comment.post_id,
        "user_id": new_comment.user_id,
        "author_name": new_comment.author_name,
        "content": new_comment.content,
        "created_at": new_comment.created_at.isoformat()
    }


@router.get("/posts/{post_id}/comments", response_model=List[CommentResponseSchema])
def get_comments(post_id: int, db: Session = Depends(get_db)):
    """Get comments for a specific post."""
    post = db.query(CommunityPost).filter(CommunityPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
        
    comments = db.query(CommunityComment).filter(CommunityComment.post_id == post_id).order_by(CommunityComment.created_at.asc()).all()
    
    return [
        {
            "id": c.id,
            "post_id": c.post_id,
            "user_id": c.user_id,
            "author_name": c.author_name,
            "content": c.content,
            "created_at": c.created_at.isoformat()
        } for c in comments
    ]
