"""
Pydantic models for request/response validation
"""
from pydantic import BaseModel, Field
from typing import Optional


class ProfileData(BaseModel):
    """Profile data extracted from video"""
    name: str = Field(default="Not specified")
    profession: str = Field(default="Not specified")
    experience: str = Field(default="Not specified")
    education: str = Field(default="Not specified")
    technologies: str = Field(default="Not specified")
    languages: str = Field(default="Not specified")
    achievements: str = Field(default="Not specified")
    soft_skills: str = Field(default="Not specified")


class TechnicalTestRequest(BaseModel):
    """Request model for technical test generation"""
    profession: str = Field(..., description="Candidate's profession")
    technologies: str = Field(..., description="Technologies and skills")
    experience: Optional[str] = Field("Not specified", description="Years of experience")
    education: Optional[str] = Field("Not specified", description="Educational background")


class VideoUploadResponse(BaseModel):
    """Response model for video upload"""
    cv_profile: str
    profile_data: ProfileData


class TechnicalTestResponse(BaseModel):
    """Response model for technical test generation"""
    technical_test_markdown: str
    profile_summary: dict
