# FlowGrid — Local Environment Setup Guide

This guide provides step-by-step instructions for setting up and running both the **Python FastAPI backend** and the **React + Vite frontend** on your local development machine.

---

## 1. What is a Python Virtual Environment?

In Python, a **Virtual Environment (`venv`)** is an isolated workspace on your computer containing its own Python interpreter and set of installed packages.

### Why do we need it?
* **Prevents Dependency Conflicts**: Different projects might require different versions of libraries (e.g., FastAPI or Pydantic). A virtual environment prevents global library clashes.
* **Keeps Your Operating System Clean**: Installed packages stay inside the local project folder rather than polluting system-wide Python.
* **Reproducibility**: Ensures every developer and deployment environment uses the exact dependencies listed in `requirements.txt`.

---

## 2. Backend Setup (Python FastAPI)

### Step 2.1: Open Terminal & Navigate to Backend
Open a terminal (PowerShell or Command Prompt on Windows, or Bash/Zsh on macOS/Linux) and navigate to the `backend/` folder:

```powershell
# From the project root (FlowGrid)
cd backend
```

### Step 2.2: Create the Virtual Environment
Run the Python `venv` module to create a new virtual environment directory named `venv`:

```powershell
python -m venv venv
```
*(This creates a folder named `venv/` inside `backend/`, which contains a private copy of Python and pip. This folder is ignored by `.gitignore`.)*

### Step 2.3: Activate the Virtual Environment

#### On Windows (PowerShell):
```powershell
.\venv\Scripts\Activate.ps1
```
> **Note for Windows Users**: If you see an error stating that *“running scripts is disabled on this system”*, allow scripts for your current session by running:
> ```powershell
> Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
> .\venv\Scripts\Activate.ps1
> ```

#### On Windows (Command Prompt):
```cmd
.\venv\Scripts\activate.bat
```

#### On macOS / Linux:
```bash
source venv/bin/activate
```

*When activated, your terminal prompt will be prefixed with `(venv)`.*

### Step 2.4: Upgrade pip & Install Dependencies
With `(venv)` active, run:

```powershell
# Recommended: upgrade pip
python -m pip install --upgrade pip

# Install FlowGrid backend dependencies
pip install -r requirements.txt
```

### Step 2.5: Configure Environment Variables
Copy the example environment file:

```powershell
# On Windows PowerShell:
Copy-Item .env.example .env

# On macOS / Linux:
cp .env.example .env
```

### Step 2.6: Run the FastAPI Development Server
Start the Uvicorn ASGI server with live reloading enabled:

```powershell
uvicorn app.main:app --reload --port 8000
```

* `--reload`: Automatically reloads the server whenever you edit and save Python code.
* `--port 8000`: Binds the server to port 8000 (`http://127.0.0.1:8000`).

### Step 2.7: Test the Backend
Open your web browser or use curl to check the endpoints:
* **Health Check**: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health) — should return `{"status": "healthy", "application": "FlowGrid"}`
* **Interactive Swagger Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
* **Alternative ReDoc Docs**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

### Step 2.8: Run Automated Tests
In a new terminal with the `(venv)` activated in the `backend/` directory:

```powershell
pytest
```

---

## 3. Frontend Setup (React + Vite)

### Step 3.1: Open a Terminal & Navigate to Frontend
Open a separate terminal window and navigate to the `frontend/` folder:

```powershell
# From the project root (FlowGrid)
cd frontend
```

### Step 3.2: Install Node Dependencies
```powershell
npm install
```

### Step 3.3: Start the Vite Development Server
```powershell
npm run dev
```

* Vite will spin up a local development server at [http://localhost:5173](http://localhost:5173).
* Open that URL in your browser to view the FlowGrid interface.

---

## 4. How Frontend and Backend Communicate

```
+------------------------------------+          +------------------------------------+
|         React + Vite               |          |          FastAPI Server            |
|       (Frontend Client)            |  HTTP    |         (Backend Service)          |
|    http://localhost:5173           | -------> |       http://127.0.0.1:8000        |
|                                    |  (CORS)  |                                    |
|  - UI Components                   | <------- |  - Validates endpoints             |
|  - State Management                |  JSON    |  - Health checks & DB operations   |
+------------------------------------+          +------------------------------------+
```

* **Cross-Origin Resource Sharing (CORS)**: The FastAPI backend in `backend/app/main.py` is configured to accept requests from `http://localhost:5173`.
* As you build features in upcoming phases, React components will fetch JSON data from `http://127.0.0.1:8000/api/...`.

---

## 5. Deactivating & Leaving the Environment

When you are done developing on the backend, you can exit the virtual environment by typing:
```powershell
deactivate
```
This restores your terminal session back to the default global Python environment.
