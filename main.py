import os
import sqlite3
from contextlib import asynccontextmanager
from datetime import date
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, HTTPException, Query, Response, status
from pydantic import BaseModel, EmailStr, Field, ValidationError, model_validator


class StudentFields(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    date_of_birth: date
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=40)
    course: str | None = Field(default=None, max_length=120)
    address: str | None = Field(default=None, max_length=300)
    enrollment_date: date | None = None


class StudentCreate(StudentFields):
    @model_validator(mode="after")
    def require_contact(self):
        if not self.email and not self.phone:
            raise ValueError("At least one of email or phone is required")
        return self


class StudentPatch(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    date_of_birth: date | None = None
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=40)
    course: str | None = Field(default=None, max_length=120)
    address: str | None = Field(default=None, max_length=300)
    enrollment_date: date | None = None


class Student(StudentFields):
    student_id: int


def create_app(database_path: str | Path | None = None) -> FastAPI:
    db_path = Path(database_path or os.getenv("STUDENTS_DB_PATH", "students.db"))

    def connect() -> sqlite3.Connection:
        connection = sqlite3.connect(db_path)
        connection.row_factory = sqlite3.Row
        return connection

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        db_path.parent.mkdir(parents=True, exist_ok=True)
        with connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS students (
                    student_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    date_of_birth TEXT NOT NULL,
                    email TEXT,
                    phone TEXT,
                    course TEXT,
                    address TEXT,
                    enrollment_date TEXT
                )
                """
            )
        yield

    app = FastAPI(title="Student Records API", version="1.0.0", lifespan=lifespan)

    @app.post("/students", response_model=Student, status_code=status.HTTP_201_CREATED)
    def create_student(student: StudentCreate):
        values = student.model_dump(mode="json")
        with connect() as connection:
            cursor = connection.execute(
                """INSERT INTO students
                   (name, date_of_birth, email, phone, course, address, enrollment_date)
                   VALUES (:name, :date_of_birth, :email, :phone, :course, :address, :enrollment_date)""",
                values,
            )
            row = connection.execute(
                "SELECT * FROM students WHERE student_id = ?", (cursor.lastrowid,)
            ).fetchone()
        return dict(row)

    @app.get("/students", response_model=list[Student])
    def list_students(
        name: Annotated[str | None, Query(min_length=1)] = None,
        course: Annotated[str | None, Query(min_length=1)] = None,
        dob_after: date | None = None,
        dob_before: date | None = None,
    ):
        conditions = []
        parameters: list[str] = []
        if name:
            conditions.append("name LIKE ? COLLATE NOCASE")
            parameters.append(f"%{name}%")
        if course:
            conditions.append("course LIKE ? COLLATE NOCASE")
            parameters.append(f"%{course}%")
        if dob_after:
            conditions.append("date_of_birth > ?")
            parameters.append(dob_after.isoformat())
        if dob_before:
            conditions.append("date_of_birth < ?")
            parameters.append(dob_before.isoformat())
        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        with connect() as connection:
            rows = connection.execute(
                f"SELECT * FROM students {where} ORDER BY student_id", parameters
            ).fetchall()
        return [dict(row) for row in rows]

    @app.get("/students/{student_id}", response_model=Student)
    def get_student(student_id: int):
        with connect() as connection:
            row = connection.execute(
                "SELECT * FROM students WHERE student_id = ?", (student_id,)
            ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Student not found")
        return dict(row)

    @app.put("/students/{student_id}", response_model=Student)
    def replace_student(student_id: int, student: StudentCreate):
        values = student.model_dump(mode="json")
        with connect() as connection:
            cursor = connection.execute(
                """UPDATE students SET name = :name, date_of_birth = :date_of_birth,
                   email = :email, phone = :phone, course = :course, address = :address,
                   enrollment_date = :enrollment_date WHERE student_id = :student_id""",
                {**values, "student_id": student_id},
            )
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Student not found")
            row = connection.execute(
                "SELECT * FROM students WHERE student_id = ?", (student_id,)
            ).fetchone()
        return dict(row)

    @app.patch("/students/{student_id}", response_model=Student)
    def update_student(student_id: int, changes: StudentPatch):
        with connect() as connection:
            row = connection.execute(
                "SELECT * FROM students WHERE student_id = ?", (student_id,)
            ).fetchone()
            if row is None:
                raise HTTPException(status_code=404, detail="Student not found")
            updated = {**dict(row), **changes.model_dump(exclude_unset=True)}
            try:
                student = StudentCreate.model_validate(
                    {key: value for key, value in updated.items() if key != "student_id"}
                )
            except ValidationError as error:
                raise HTTPException(
                    status_code=422, detail=error.errors(include_context=False)
                ) from error
            values = student.model_dump(mode="json")
            connection.execute(
                """UPDATE students SET name = :name, date_of_birth = :date_of_birth,
                   email = :email, phone = :phone, course = :course, address = :address,
                   enrollment_date = :enrollment_date WHERE student_id = :student_id""",
                {**values, "student_id": student_id},
            )
            result = connection.execute(
                "SELECT * FROM students WHERE student_id = ?", (student_id,)
            ).fetchone()
        return dict(result)

    @app.delete("/students/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
    def delete_student(student_id: int):
        with connect() as connection:
            cursor = connection.execute(
                "DELETE FROM students WHERE student_id = ?", (student_id,)
            )
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Student not found")
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    return app


app = create_app()