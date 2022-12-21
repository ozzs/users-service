# users-service

## Usage

To start, run

    docker-compose up --build

### Step 1: Create and read user

To create a new user,

    POST /users/
    {
        "name": "Harry Potter",
        "email": "harry@potter.com",
        "age": 53,
        "gender": "male",
        "house": "gryffindor",
        "blood_status": "pure_blood"
    }

This will return the user's ID. You can read it by calling `GET /users/<ID>`.

### Step 2: Update user

To update a user,

    PATCH /users/<USER_ID>
    {
        "age": 53,
        "gender": "male",
    }

This will run async using Celery. The API will return the task ID, e.g:

    {
        "task_id": "a1adedda-9c1e-4ec5-83e3-037cb7bd96e4"
    }

You can now query the task by:

    GET /tasks/a1adedda-9c1e-4ec5-83e3-037cb7bd96e4

    {
        "id": "a1adedda-9c1e-4ec5-83e3-037cb7bd96e4",
        "status": "SUCCESS",
        "result": {
            "created_at": "2022-12-17T10:36:44.281481",
            "gender": "male",
            "name": "HARRY",
            "age": null,
            "deleted_at": null,
            "house": "slytherin",
            "blood_status": "pure_blood",
            "updated_at": "2022-12-17T12:50:00.518738",
            "email": "malfoy@potter.com",
            "id": 4
        }
    }

### Step 3: Delete user

To delete a user,

    DELETE /users/<ID>

This will soft delete the user - its data will still exist in the database. 
This API simply updates `deleted_at`, and all other APIs make sure to ignore any users with `deleted_at != NULL`.

## Tests

To run tests

    poetry install
    poetry run pytest

## Linting & Formatting

To format code

    poetry run black .
    poetry run isort .

To run lint

    poetry run flake8

