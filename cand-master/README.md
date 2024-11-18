# Candidate Management  API

This project is a RESTful API built with **FastAPI** for managing candidates, requirements, and clients. It interacts with a **MySQL** database and provides endpoints for creating, retrieving, updating, and deleting candidate records.

## Features

- Retrieve a list of all clients
- Retrieve a list of all requirements
- Create a new candidate for a specific requirement
- Retrieve all candidates
- Retrieve a candidate by ID
- Update candidate details
- Delete a candidate by ID

## Technologies Used

- **FastAPI**: A modern, fast (high-performance) web framework for building APIs with Python 3.7+.
- **MySQL**: A relational database management system used to store and manage candidate data.
- **Pydantic**: Data validation and settings management using Python type annotations.
- **CORS Middleware**: To allow cross-origin requests.
- **dotenv**: Used to manage environment variables securely.

## Prerequisites

- **Python 3.7+**
- **MySQL**
- **pip** (Python package manager)
- **FastAPI** and **Uvicorn** for running the server.

## Installation

1. **Clone the repository**:
    ```bash
    git clone https://github.com/yourusername/candidate-management-api.git
    cd candidate-management-api
    ```

2. **Set up a virtual environment** (optional but recommended):
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. **Install the required packages**:
    ```bash
    pip install -r requirements.txt
    ```

4. **Create a `.env` file**:
    Create a `.env` file in the project root and add your MySQL database credentials.
    ```
    MYSQL_HOST=your_mysql_host
    MYSQL_USER=your_mysql_user
    MYSQL_PASSWORD=your_mysql_password
    MYSQL_DB=your_database_name
    ```

5. **Run the application**:
    ```bash
    uvicorn main:app --reload --host 0.0.0.0 --port 8007
    ```

6. **Access the API documentation**:
    After running the application, navigate to `http://localhost:8007/docs` to access the automatically generated Swagger UI documentation.

## API Endpoints

### 1. Get all clients

- **URL**: `/clients`
- **Method**: `GET`
- **Response**: List of clients with `cl_id` and `cl_name`.

### 2. Get all requirements

- **URL**: `/requirements`
- **Method**: `GET`
- **Response**: List of requirements with `rq_id` and `rq_name`.

### 3. Create a new candidate for a specific requirement

- **URL**: `/candidates/{rq_id}`
- **Method**: `POST`
- **Request Body**: Candidate object
- **Response**: Message and candidate ID.

### 4. Get all candidates

- **URL**: `/candidates`
- **Method**: `GET`
- **Response**: List of candidates.

### 5. Get a specific candidate by ID

- **URL**: `/candidates/{cd_id}`
- **Method**: `GET`
- **Response**: Candidate details.

### 6. Update a candidate by ID

- **URL**: `/candidates/{cd_id}`
- **Method**: `PUT`
- **Request Body**: Candidate object
- **Response**: Success message.

### 7. Delete a candidate by ID

- **URL**: `/candidates/{cd_id}`
- **Method**: `DELETE`
- **Response**: Success message.

## Database Schema

### `clients` Table

| Field   | Type   | Description  |
|---------|--------|--------------|
| cl_id   | string | Client ID    |
| cl_name | string | Client name  |

### `requirements` Table

| Field   | Type   | Description        |
|---------|--------|--------------------|
| rq_id   | string | Requirement ID     |
| rq_name | string | Requirement name   |

### `candidates` Table

| Field            | Type    | Description                           |
|------------------|---------|---------------------------------------|
| cd_id            | string  | Candidate ID (UUID)                   |
| rq_id            | string  | Requirement ID (Foreign Key)          |
| cd_first_name    | string  | Candidate's first name                |
| cd_last_name     | string  | Candidate's last name (optional)      |
| cd_email         | string  | Candidate's email (validated)         |
| cd_phno          | string  | Candidate's phone number              |
| cd_qual          | string  | Candidate's qualification             |
| cd_total_exp     | int     | Candidate's total experience (years)  |
| cd_related_exp   | int     | Related experience (optional)         |
| cd_loc           | string  | Candidate's location                  |
| cd_cur_ctc       | float   | Current CTC                           |
| cd_exp_ctc       | float   | Expected CTC                          |
| cd_notice        | string  | Notice period                         |
| cd_work_mode     | string  | Work mode (e.g., Remote, On-site)     |
| cd_valid_passport| boolean | Passport status (optional)            |
| created_by       | string  | Creator information (optional)        |

## Environment Variables

Make sure to create a `.env` file with the following variables:


MYSQL_HOST=your_mysql_host
MYSQL_USER=your_mysql_user
MYSQL_PASSWORD=your_mysql_password
MYSQL_DB=your_database_name



## Error Handling

The API returns appropriate HTTP status codes and error messages in case of failures, such as:
- `404 Not Found`: If the requested resource (client or requirement) is not found.
- `500 Internal Server Error`: For issues with database connections or queries.

## License

This project is licensed under the "....." License. See the [LICENSE](LICENSE) file for details.

## Contact

For any queries or support, please reach out to sandeeprajendra00@gmail.com

