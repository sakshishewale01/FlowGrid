# FlowGrid — Database Setup & Migrations Guide
**PostgreSQL + SQLAlchemy 2.0 + Alembic**

This guide walks you through setting up a local PostgreSQL database, configuring environment variables, verifying connectivity, and managing database schema migrations using Alembic for **FlowGrid Phase 2**.

---

## 1. Prerequisites & Architecture

FlowGrid uses:
* **Database Engine**: PostgreSQL (v14, v15, or v16 recommended)
* **Python ORM**: SQLAlchemy 2.0 (synchronous engine with declarative mapping)
* **PostgreSQL Driver**: `psycopg` (v3 with binary extension)
* **Schema Migration Tool**: Alembic
* **Connection Dialect**: `postgresql+psycopg://<username>:<password>@<host>:<port>/<dbname>`

---

## 2. Step 1: Install and Start PostgreSQL

Choose one of the following methods to run PostgreSQL on your machine:

### Option A: Standard Windows Installer (Recommended for Beginners)
1. Download the PostgreSQL installer for Windows from the official website:
   👉 [https://www.postgresql.org/download/windows/](https://www.postgresql.org/download/windows/)
2. Run the installer:
   * Keep default port: `5432`
   * Set a password for the default `postgres` user (e.g., `postgres` or your custom password).
   * Install the command line tools and pgAdmin.
3. Verify that the PostgreSQL service is running in Windows Services (`services.msc`).

### Option B: Docker (Alternative)
If you have Docker Desktop installed, you can spin up an isolated PostgreSQL container with one command:

```powershell
docker run -d `
  --name flowgrid-postgres `
  -e POSTGRES_USER=postgres `
  -e POSTGRES_PASSWORD=postgres `
  -e POSTGRES_DB=flowgrid_db `
  -p 5432:5432 `
  postgres:16-alpine
```

### Option C: macOS (Homebrew)
```bash
brew install postgresql@16
brew services start postgresql@16
```

### Option D: Linux (Ubuntu / Debian)
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
```

---

## 3. Step 2: Create the `flowgrid_db` Database

Open your terminal or `psql` command line tool:

```powershell
# Connect to PostgreSQL as superuser
psql -U postgres
```

Inside the SQL prompt, run:

```sql
-- 1. Create the dedicated database for FlowGrid
CREATE DATABASE flowgrid_db;

-- 2. Verify creation (optional)
\l

-- 3. Exit psql
\q
```

*(Note: If you use pgAdmin, right-click on **Databases** ➔ **Create** ➔ **Database...**, name it `flowgrid_db`, and click Save.)*

---

## 4. Step 3: Configure `.env` in `backend/`

Open `backend/.env` (or copy from `backend/.env.example` if not already created):

```powershell
cd backend
Copy-Item .env.example .env
```

Ensure the `DATABASE_URL` matches your local PostgreSQL credentials:

```env
# Database Configuration (PostgreSQL + SQLAlchemy 2.0 + psycopg 3)
DATABASE_URL=postgresql+psycopg://postgres:YOUR_PASSWORD@localhost:5432/flowgrid_db
```

### URL Format Breakdown:
```
postgresql+psycopg://  postgres   :  password  @  localhost : 5432  /  flowgrid_db
       │                  │              │            │        │            │
    Dialect            Username       Password      Host     Port     Database Name
```

> **Security Note**: Never commit actual database passwords to Git. The `.gitignore` file is configured to keep `.env` out of version control.

---

## 5. Step 4: Verify Database Connectivity

FlowGrid provides a dedicated safe diagnostic endpoint to test database health without interrupting the application.

1. Activate your virtual environment and start the FastAPI server:
   ```powershell
   cd backend
   .\venv\Scripts\Activate.ps1
   uvicorn app.main:app --reload --port 8000
   ```

2. Open the database health check endpoint in your browser or curl:
   👉 **[http://127.0.0.1:8000/health/db](http://127.0.0.1:8000/health/db)**

   * **When Connected**:
     ```json
     {
       "status": "connected",
       "database_connected": true,
       "detail": "Database connection successful"
     }
     ```

   * **If Offline / Incorrect Credentials**:
     ```json
     {
       "status": "disconnected",
       "database_connected": false,
       "detail": "connection to server at \"localhost\" (127.0.0.1), port 5432 failed..."
     }
     ```
     *(The endpoint returns HTTP 200 with clear diagnostics instead of an unhandled crash.)*

3. Standard health check remains unaffected:
   👉 **[http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)**
   ```json
   {
     "status": "healthy",
     "application": "FlowGrid"
   }
   ```

---

## 6. Step 5: Managing Database Migrations with Alembic

Alembic inspects your SQLAlchemy models (inheriting from `app.db.base.Base`) and compares them against your PostgreSQL schema to generate versioned migration scripts.

### 6.1 Creating a Migration Script
In future phases when tables are added to `app/models/`, generate a migration:

```powershell
# From the backend/ directory with (venv) active:
alembic revision --autogenerate -m "create initial tables"
```
*This generates a new Python migration script inside `backend/alembic/versions/`.*

### 6.2 Applying Migrations (Upgrading Database)
To apply all pending migrations to your PostgreSQL database:

```powershell
alembic upgrade head
```

### 6.3 Checking Migration Status
```powershell
# Show current database revision
alembic current

# Show complete revision history
alembic history --verbose
```

### 6.4 Rolling Back Migrations (Downgrading)
To revert the most recent migration:

```powershell
alembic downgrade -1
```

---

## 7. Common Troubleshooting

| Issue | Cause | Solution |
| :--- | :--- | :--- |
| `connection refused at localhost:5432` | PostgreSQL service is not started | Open Windows Services (`services.msc`) and start `postgresql-x64-XX`, or run your Docker container. |
| `password authentication failed for user "postgres"` | Incorrect password in `.env` | Update `DATABASE_URL` in `backend/.env` with the password you set during installation. |
| `database "flowgrid_db" does not exist` | Database has not been created yet | Run `CREATE DATABASE flowgrid_db;` in `psql` or create it in pgAdmin. |
| `No module named 'psycopg'` | Dependency missing in active environment | Ensure `(venv)` is activated and run `pip install -r requirements.txt`. |
