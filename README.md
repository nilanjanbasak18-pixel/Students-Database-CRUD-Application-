# Student Records API

A small REST API for creating, searching, updating, and deleting student records. FastAPI provides the HTTP interface and SQLite stores records in a local database file.

## Prerequisites

- Python 3.10 or newer
- `pip`

## Install and run

From the project directory, create and activate a virtual environment, then install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Start the API:

```bash
uvicorn main:app --reload
```

The API is available at `http://127.0.0.1:8000`. SQLite creates `students.db` in the current directory on first startup. Set `STUDENTS_DB_PATH` to use a different file path. Interactive API documentation is at `http://127.0.0.1:8000/docs`.

## API

| Method | Endpoint | Description |
| --- | --- | --- |
| `POST` | `/students` | Create a student |
| `GET` | `/students` | List students; optionally filter by `name`, `course`, `dob_after`, or `dob_before` |
| `GET` | `/students/{student_id}` | Retrieve one student |
| `PUT` | `/students/{student_id}` | Replace a student's details |
| `PATCH` | `/students/{student_id}` | Update selected details |
| `DELETE` | `/students/{student_id}` | Delete a student |

Each student has a generated integer `student_id`, required `name` and ISO-format `date_of_birth`, and at least one of `email` or `phone`. `course`, `address`, and ISO-format `enrollment_date` are optional. Invalid input returns `422`; operations on a missing student return `404`.

## Try it

Create a record (use dummy data):

```bash
curl -X POST http://127.0.0.1:8000/students \
	-H 'Content-Type: application/json' \
	-d '{"name":"Avery Chen","date_of_birth":"2005-04-12","email":"avery@example.com","course":"Biology"}'
```

List students born after 2005-01-01:

```bash
curl 'http://127.0.0.1:8000/students?dob_after=2005-01-01'
```

Update a record (replace `1` with the returned ID):

```bash
curl -X PATCH http://127.0.0.1:8000/students/1 \
	-H 'Content-Type: application/json' \
	-d '{"phone":"555-0100"}'
```

Delete a record:

```bash
curl -X DELETE http://127.0.0.1:8000/students/1
```

## Tests

```bash
python -m pytest
```

Tests use temporary SQLite databases and synthetic records. No real student data or credentials are included. The optional Ollama extension is not included; the core CRUD API works independently.