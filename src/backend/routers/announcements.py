"""
Announcements router for managing system-wide announcements
"""

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, date
from ..database import announcements_collection
from .auth import get_current_user
from bson import ObjectId

router = APIRouter(prefix="/api/announcements", tags=["announcements"])


class AnnouncementCreate(BaseModel):
    message: str = Field(..., min_length=1, max_length=500)
    start_date: Optional[str] = None  # ISO date string (YYYY-MM-DD)
    end_date: str  # ISO date string (YYYY-MM-DD), required


class AnnouncementUpdate(BaseModel):
    message: Optional[str] = Field(None, min_length=1, max_length=500)
    start_date: Optional[str] = None
    end_date: Optional[str] = None


@router.get("")
async def get_active_announcements():
    """Get all currently active announcements (public endpoint)"""
    try:
        today = date.today().isoformat()
        announcements = list(announcements_collection.find())
        
        # Filter active announcements
        active_announcements = []
        for announcement in announcements:
            start_date = announcement.get("start_date")
            end_date = announcement.get("end_date")
            
            # Check if announcement is active
            is_active = True
            if start_date and start_date > today:
                is_active = False
            if end_date and end_date < today:
                is_active = False
            
            if is_active:
                # Convert ObjectId to string for JSON serialization
                announcement["_id"] = str(announcement["_id"])
                active_announcements.append(announcement)
        
        return {"announcements": active_announcements}
    except Exception as e:
        print(f"Error fetching announcements: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch announcements"
        )


@router.get("/all")
async def get_all_announcements(current_user: dict = Depends(get_current_user)):
    """Get all announcements including expired ones (requires authentication)"""
    try:
        announcements = list(announcements_collection.find())
        
        # Convert ObjectId to string for JSON serialization
        for announcement in announcements:
            announcement["_id"] = str(announcement["_id"])
        
        return {"announcements": announcements}
    except Exception as e:
        print(f"Error fetching all announcements: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch announcements"
        )


@router.post("")
async def create_announcement(
    announcement: AnnouncementCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new announcement (requires authentication)"""
    try:
        # Validate dates
        if announcement.start_date:
            try:
                datetime.fromisoformat(announcement.start_date)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid start_date format. Use YYYY-MM-DD"
                )
        
        try:
            datetime.fromisoformat(announcement.end_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid end_date format. Use YYYY-MM-DD"
            )
        
        # Check if end_date is after start_date
        if announcement.start_date and announcement.end_date:
            if announcement.start_date > announcement.end_date:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="end_date must be after start_date"
                )
        
        announcement_data = announcement.dict()
        result = announcements_collection.insert_one(announcement_data)
        
        announcement_data["_id"] = str(result.inserted_id)
        return {"message": "Announcement created successfully", "announcement": announcement_data}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error creating announcement: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create announcement"
        )


@router.put("/{announcement_id}")
async def update_announcement(
    announcement_id: str,
    announcement: AnnouncementUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update an existing announcement (requires authentication)"""
    try:
        # Validate ObjectId
        try:
            obj_id = ObjectId(announcement_id)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid announcement ID"
            )
        
        # Build update data (only include provided fields)
        update_data = {}
        if announcement.message is not None:
            update_data["message"] = announcement.message
        if announcement.start_date is not None:
            try:
                datetime.fromisoformat(announcement.start_date)
                update_data["start_date"] = announcement.start_date
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid start_date format. Use YYYY-MM-DD"
                )
        if announcement.end_date is not None:
            try:
                datetime.fromisoformat(announcement.end_date)
                update_data["end_date"] = announcement.end_date
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid end_date format. Use YYYY-MM-DD"
                )
        
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update"
            )
        
        result = announcements_collection.update_one(
            {"_id": obj_id},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Announcement not found"
            )
        
        return {"message": "Announcement updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating announcement: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update announcement"
        )


@router.delete("/{announcement_id}")
async def delete_announcement(
    announcement_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete an announcement (requires authentication)"""
    try:
        # Validate ObjectId
        try:
            obj_id = ObjectId(announcement_id)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid announcement ID"
            )
        
        result = announcements_collection.delete_one({"_id": obj_id})
        
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Announcement not found"
            )
        
        return {"message": "Announcement deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting announcement: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete announcement"
        )
