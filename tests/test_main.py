from fastapi.testclient import TestClient

from main import create_app


def test_crud_filters_and_persistence(tmp_path):
    database = tmp_path / "students.db"
    with TestClient(create_app(database)) as client:
        first = client.post(
            "/students",
            json={
                "name": "Avery Chen",
                "date_of_birth": "2004-04-12",
                "email": "avery@example.com",
                "course": "Biology",
            },
        )
        second = client.post(
            "/students",
            json={
                "name": "Jordan Lee",
                "date_of_birth": "2007-09-03",
                "phone": "555-0100",
                "course": "Physics",
            },
        )
        assert first.status_code == 201
        assert second.status_code == 201
        first_id = first.json()["student_id"]
        second_id = second.json()["student_id"]

        assert len(client.get("/students").json()) == 2
        assert [item["name"] for item in client.get("/students?name=jordan").json()] == [
            "Jordan Lee"
        ]
        assert [item["student_id"] for item in client.get(
            "/students?dob_after=2005-01-01&course=phys"
        ).json()] == [second_id]
        assert client.get(f"/students/{first_id}").json()["email"] == "avery@example.com"

        replaced = client.put(
            f"/students/{first_id}",
            json={
                "name": "Avery Chen",
                "date_of_birth": "2004-04-12",
                "email": "avery@example.com",
                "course": "Chemistry",
                "enrollment_date": "2023-09-01",
            },
        )
        assert replaced.status_code == 200
        assert replaced.json()["course"] == "Chemistry"
        patched = client.patch(f"/students/{first_id}", json={"phone": "555-0101"})
        assert patched.status_code == 200
        assert patched.json()["email"] == "avery@example.com"
        assert patched.json()["phone"] == "555-0101"

    with TestClient(create_app(database)) as client:
        assert client.get(f"/students/{first_id}").status_code == 200
        assert client.delete(f"/students/{first_id}").status_code == 204
        assert client.get(f"/students/{first_id}").status_code == 404
        assert client.delete(f"/students/{first_id}").status_code == 404


def test_validation_and_missing_record_handling(tmp_path):
    with TestClient(create_app(tmp_path / "students.db")) as client:
        no_contact = client.post(
            "/students", json={"name": "Casey", "date_of_birth": "2005-02-03"}
        )
        invalid_date = client.post(
            "/students",
            json={
                "name": "Casey",
                "date_of_birth": "2005-02-30",
                "email": "casey@example.com",
            },
        )
        assert no_contact.status_code == 422
        assert invalid_date.status_code == 422
        assert client.get("/students/999").status_code == 404
        assert client.put(
            "/students/999",
            json={
                "name": "Casey",
                "date_of_birth": "2005-02-03",
                "email": "casey@example.com",
            },
        ).status_code == 404

        created = client.post(
            "/students",
            json={
                "name": "Casey",
                "date_of_birth": "2005-02-03",
                "email": "casey@example.com",
            },
        )
        student_id = created.json()["student_id"]
        assert client.patch(
            f"/students/{student_id}", json={"email": None}
        ).status_code == 422