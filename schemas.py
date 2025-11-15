"""
Database Schemas for School Management App

Each Pydantic model represents a collection in MongoDB.
The collection name is the lowercase class name.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
import datetime as dt


class Student(BaseModel):
    name: str = Field(..., description="Full name")
    roll_no: str = Field(..., description="Roll number or ID")
    class_name: str = Field(..., description="Class/Grade, e.g., 6A")
    section: Optional[str] = Field(None, description="Optional section")


class Note(BaseModel):
    subject: str = Field(...)
    title: str = Field(...)
    content: str = Field(...)
    class_name: str = Field(...)


class Assignment(BaseModel):
    subject: str = Field(...)
    title: str = Field(...)
    description: str = Field(...)
    due_date: dt.date = Field(...)
    class_name: str = Field(...)


class Worksheet(BaseModel):
    subject: str = Field(...)
    title: str = Field(...)
    description: Optional[str] = Field(None)
    class_name: str = Field(...)


class Circular(BaseModel):
    title: str
    message: str
    audience: str = Field(..., description="e.g., all, teachers, class-6A")


class Event(BaseModel):
    title: str
    date: dt.date
    location: Optional[str] = None
    description: Optional[str] = None


class Attendance(BaseModel):
    student_id: str = Field(..., description="Reference to student _id")
    date: dt.date = Field(...)
    status: str = Field(..., description="present/absent")


class Upload(BaseModel):
    filename: str
    path: str
    uploaded_by: str = Field(..., description="teacher name or id")
    subject: Optional[str] = None
    class_name: Optional[str] = None
