import os
from datetime import date
from typing import List, Optional

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from pydantic import BaseModel

from database import db, create_document, get_documents
from schemas import Student, Note, Assignment, Worksheet, Circular, Event, Attendance, Upload

app = FastAPI(title="School Management API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "School Management Backend is running"}


@app.get("/test")
def test_database():
    result = {
        "backend": "✅ Running",
        "database": "❌ Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            result["database"] = "✅ Connected"
            try:
                result["collections"] = db.list_collection_names()[:10]
            except Exception:
                pass
    except Exception as e:
        result["database"] = f"❌ Error: {str(e)[:80]}"
    return result


# --------------------------- Students ---------------------------
class BulkStudents(BaseModel):
    students: List[Student]


@app.post("/api/students", response_model=dict)
def add_student(student: Student):
    student_id = create_document("student", student)
    return {"_id": student_id}


@app.post("/api/students/bulk", response_model=dict)
def add_students_bulk(payload: BulkStudents):
    inserted_ids: List[str] = []
    for s in payload.students:
        inserted_ids.append(create_document("student", s))
    return {"inserted": inserted_ids}


@app.get("/api/students", response_model=List[dict])
def list_students(class_name: Optional[str] = None):
    filt = {"class_name": class_name} if class_name else {}
    docs = get_documents("student", filt)
    # Convert ObjectId to string
    for d in docs:
        if "_id" in d:
            d["_id"] = str(d["_id"])
    return docs


# --------------------------- Notes / Assignments / Worksheets ---------------------------
@app.post("/api/notes")
def create_note(note: Note):
    _id = create_document("note", note)
    return {"_id": _id}


@app.get("/api/notes")
def get_notes(class_name: Optional[str] = None, subject: Optional[str] = None):
    filt = {}
    if class_name:
        filt["class_name"] = class_name
    if subject:
        filt["subject"] = subject
    docs = get_documents("note", filt)
    for d in docs:
        d["_id"] = str(d["_id"]) if "_id" in d else None
    return docs


@app.post("/api/assignments")
def create_assignment(assignment: Assignment):
    _id = create_document("assignment", assignment)
    return {"_id": _id}


@app.get("/api/assignments")
def get_assignments(class_name: Optional[str] = None, subject: Optional[str] = None):
    filt = {}
    if class_name:
        filt["class_name"] = class_name
    if subject:
        filt["subject"] = subject
    docs = get_documents("assignment", filt)
    for d in docs:
        d["_id"] = str(d["_id"]) if "_id" in d else None
    return docs


@app.post("/api/worksheets")
def create_worksheet(worksheet: Worksheet):
    _id = create_document("worksheet", worksheet)
    return {"_id": _id}


@app.get("/api/worksheets")
def get_worksheets(class_name: Optional[str] = None, subject: Optional[str] = None):
    filt = {}
    if class_name:
        filt["class_name"] = class_name
    if subject:
        filt["subject"] = subject
    docs = get_documents("worksheet", filt)
    for d in docs:
        d["_id"] = str(d["_id"]) if "_id" in d else None
    return docs


# --------------------------- Circulars / Events ---------------------------
@app.post("/api/circulars")
def create_circular(c: Circular):
    _id = create_document("circular", c)
    return {"_id": _id}


@app.get("/api/circulars")
def get_circulars():
    docs = get_documents("circular")
    for d in docs:
        d["_id"] = str(d["_id"]) if "_id" in d else None
    return docs


@app.post("/api/events")
def create_event(ev: Event):
    _id = create_document("event", ev)
    return {"_id": _id}


@app.get("/api/events")
def get_events():
    docs = get_documents("event")
    for d in docs:
        d["_id"] = str(d["_id"]) if "_id" in d else None
    return docs


# --------------------------- Attendance ---------------------------
class AttendanceSet(BaseModel):
    student_id: str
    date: date
    status: str  # present/absent


@app.post("/api/attendance/set")
def set_attendance(payload: AttendanceSet):
    # Upsert by (student_id, date)
    try:
        from bson import ObjectId  # type: ignore
    except Exception:
        ObjectId = None

    filt = {"student_id": payload.student_id, "date": payload.date}
    if db is None:
        return JSONResponse(status_code=500, content={"error": "Database not available"})

    res = db["attendance"].update_one(filt, {"$set": {"status": payload.status}}, upsert=True)
    return {"matched": res.matched_count, "modified": res.modified_count, "upserted_id": str(res.upserted_id) if res.upserted_id else None}


@app.get("/api/attendance")
def get_attendance(date_value: date):
    if db is None:
        return []
    docs = list(db["attendance"].find({"date": date_value}))
    for d in docs:
        d["_id"] = str(d["_id"]) if "_id" in d else None
    return docs


# --------------------------- Uploads ---------------------------
UPLOAD_DIR = os.path.join(os.getcwd(), "uploads")

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...), uploaded_by: str = Form(...), subject: str = Form(None), class_name: str = Form(None)):
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file_location = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_location, "wb") as buffer:
        buffer.write(await file.read())

    upload_doc = Upload(filename=file.filename, path=file_location, uploaded_by=uploaded_by, subject=subject, class_name=class_name)
    _id = create_document("upload", upload_doc)
    return {"_id": _id, "filename": file.filename, "path": file_location}


@app.get("/api/uploads")
def list_uploads(class_name: Optional[str] = None, subject: Optional[str] = None):
    filt = {}
    if class_name:
        filt["class_name"] = class_name
    if subject:
        filt["subject"] = subject
    docs = get_documents("upload", filt)
    for d in docs:
        d["_id"] = str(d["_id"]) if "_id" in d else None
    return docs


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
