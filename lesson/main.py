import uvicorn
import time
import pathlib

from fastapi import FastAPI, Path, Query, Depends, HTTPException, status, Request, File, UploadFile
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from db import get_db, Note

app = FastAPI()

@app.get("/api/healthcheck")
def root():
    return {"message": "Welcome to FastAPI!"}


@app.get("/notes")
async def read_notes(skip: int = 0, limit: int = Query(default=10, le=100, ge=10)):
    return {"message": f"Return all notes: skip: {skip}, limit: {limit}"}


@app.get("/notes/{note_id}")
async def read_note(
    note_id: int = Path(
        description="The ID of the note to get",
        gt=0,
        le=10
    )
):
    return {"note": note_id}


class NoteModel(BaseModel):
    name: str
    description: str
    done: bool

@app.post("/notes")
async def create_note(note: NoteModel):
    return {"name": note.name, "description": note.description, "status": note.done}


@app.get("/api/healthchecker")
def healthchecker(db: Session = Depends(get_db)):
    try:

        # Make request
        result = db.execute("SELECT 1").fetchone()
        if result is None:
            raise HTTPException(
                status_code=500,
                detail="Database is not configured correctly"
            )

        return { "message": "Welcome to FastAPI!" }

    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=500,
            detail="Error connecting to the database"
        )


@app.post("/db_notes")
async def create_note(note: NoteModel, db: Session = Depends(get_db)):
    new_note = Note(name=note.name, description=note.description, done=note.done)
    db.add(new_note)
    db.commit()
    db.refresh(new_note)
    return new_note


class ResponseNoteModel(BaseModel):
    id: int = Field(default=1, ge=1)
    name: str
    description: str
    done: bool


@app.get("/db_notes")
async def read_notes(
    skip: int = 0, limit: int = Query(default=10, le=100, ge=10),
    db: Session = Depends(get_db)
) -> list[ResponseNoteModel]:
    notes = db.query(Note).offset(skip).limit(limit).all()
    return notes


@app.get("/db_notes/{note_id}", response_model=ResponseNoteModel)
async def read_note(note_id: int = Path(description="The ID of the note to get", gt=0, le=10),
                    db: Session = Depends(get_db)):

    note = db.query(Note).filter(Note.id == note_id).first()

    if note is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Not found'
        )

    return note


@app.exception_handler(HTTPException)
def handle_http_exception(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail},
    )

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


@app.post("/uploadfile/")
async def create_upload_file(file: UploadFile = File()):
    pathlib.Path("uploads").mkdir(exist_ok=True)
    file_path = f"uploads/{file.filename}"
    with open(file_path, "wb") as f:
        f.write(await file.read())
    return {"file_path": file_path}


app.mount("/static", StaticFiles(directory="static"), name="static")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="localhost",
        port=8000,
        reload=True
    )
