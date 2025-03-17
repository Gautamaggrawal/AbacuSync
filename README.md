# AbacuSync


## Overview
This API provides authentication and user management functionalities for Admin, Centre, and Student users. It includes login, logout, and role-based access control to manage centres, students, and levels.

## Features
### Authentication
- **Login endpoints** for Admin, Centre, and Student users
- **Logout endpoint** to invalidate the session
- **Automatic token storage** in environment variables

### Admin - Centre Management
- **List all centres** with search capability
- **Create new centre** with Centre Instructors (CIs)
- **Get centre details**
- **Update centre information**
- **Reset centre password**
- **Toggle centre active status** (enable/disable a centre)
- **View students associated with a centre**

### Centre - Student Management
- **List students** (filtered by centre for centre users)
- **Create a new student**
- **Get student details**
- **Update student information**
- **Reset student password**
- **Toggle student active status** (enable/disable a student)
- **View student's level history**

### Admin - Student Management
- **Approve student** (admin-only functionality)

### Level Management
- **List all levels**
- **Get level details**

### Student Level History
- **List level history entries**
- **Create a new level history entry**

## API Collection Features
The Postman collection includes:
- **Environment variables** for base URL and tokens
- **Proper authentication headers**
- **Example request bodies**
- **Test scripts** to automatically store authentication tokens
- **Search parameters** where applicable
- **Descriptive names and documentation** for each request

## Usage Instructions
### 1. Import API Collection
- Download the JSON file for the API collection.
- Import it into **Postman**.

### 2. Setup Environment Variables
Create an environment in Postman with the following variables:
- `base_url` (e.g., `http://localhost:8000/api`)
- `admin_token` (auto-populated after admin login)
- `centre_token` (auto-populated after centre login)
- `student_token` (auto-populated after student login)
- `centre_uuid` (set after creating a centre)
- `student_uuid` (set after creating a student)
- `level_uuid` (set after fetching levels)
- `ci_uuid` (set after creating a centre with CIs)

### 3. Logical API Flow
1. **Login** to get the authentication token.
2. **Use the token** for subsequent requests.
3. **Create and manage centres** (admin functionality).
4. **Create and manage students** (centre functionality).
5. **Approve students** (admin functionality).
6. **Manage student levels and track history**.

## Authentication
All endpoints require authentication via **Bearer Tokens**.
- Admins manage centres and approve students.
- Centres manage students.
- Students access their own details and level history.

## API Documentation (Swagger UI)
To explore the API endpoints interactively, visit:
[Swagger Documentation](https://abacusync.onrender.com/api/schema/swagger-ui/)

## Setup Django Repository Locally
### Prerequisites
Ensure you have the following installed:
- Python (>=3.8)
- pip
- virtualenv
- PostgreSQL or SQLite (as per your settings)

### Installation Steps
1. **Clone the repository**
   ```sh
   git clone <repository_url>
   cd <repository_directory>
   ```

2. **Create and activate a virtual environment**
   ```sh
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install dependencies**
   ```sh
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   - Create a `.env` file in the project root.
   - Add the necessary environment variables (e.g., database credentials, secret keys).

5. **Apply database migrations**
   ```sh
   python manage.py migrate
   ```

6. **Create a superuser (for admin access)**
   ```sh
   python manage.py createsuperuser
   ```

7. **Run the development server**
   ```sh
   python manage.py runserver
   ```

8. **Access the API**
   - Open `http://localhost:8000/api/` in your browser or use Postman.
   - View API documentation at [Swagger UI](https://abacusync.onrender.com/api/schema/swagger-ui/).

## Contact
For any queries or support, contact the development team.