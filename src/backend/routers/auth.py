"""
Authentication endpoints for the High School Management System API
"""

from fastapi import APIRouter, HTTPException, Header
from typing import Dict, Any, Optional

from ..database import teachers_collection, verify_password

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)


async def get_current_user(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """
    Dependency function to get the current authenticated user.
    For simplicity, we're using a basic token scheme where the token is the username.
    In production, use proper JWT tokens.
    """
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated"
        )
    
    # For this simple implementation, the "token" is just the username
    # In production, decode and validate a JWT token here
    username = authorization.replace("Bearer ", "")
    
    teacher = teachers_collection.find_one({"_id": username})
    
    if not teacher:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials"
        )
    
    return {
        "username": teacher["username"],
        "display_name": teacher["display_name"],
        "role": teacher["role"]
    }


@router.post("/login")
def login(username: str, password: str) -> Dict[str, Any]:
    """Login a teacher account"""
    # Find the teacher in the database
    teacher = teachers_collection.find_one({"_id": username})

    # Verify password using Argon2 verifier from database.py
    if not teacher or not verify_password(teacher.get("password", ""), password):
        raise HTTPException(
            status_code=401, detail="Invalid username or password")

    # Return teacher information (excluding password)
    return {
        "username": teacher["username"],
        "display_name": teacher["display_name"],
        "role": teacher["role"]
    }


@router.get("/check-session")
def check_session(username: str) -> Dict[str, Any]:
    """Check if a session is valid by username"""
    teacher = teachers_collection.find_one({"_id": username})

    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")

    return {
        "username": teacher["username"],
        "display_name": teacher["display_name"],
        "role": teacher["role"]
    }
