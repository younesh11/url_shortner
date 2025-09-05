# URL Shortener - Setup & Running Guide

A complete guide to set up and run the URL Shortener application with FastAPI backend and Streamlit frontend.

## Prerequisites

- Python 3.11 or higher
- Git
- pip (Python package manager)

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone ttps://github.com/younesh11/url_shortner/
cd url-shortener
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```
### 4. setup environment variables

## 🗄️ Database Setup

### Initialize the Database

```bash
cd backend
python -m app.db.init_db
```

This will create the necessary database tables and structure for the URL shortener service.

## 🖥️ Running the Application

### Backend Service (FastAPI)

1. **Navigate to backend directory** (if not already there):
   ```bash
   cd backend
   ```

2. **Start the FastAPI server**:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

   The backend API will be available at: `http://localhost:8000`
   
   - API documentation: `http://localhost:8000/docs`
  

### Frontend Service (Streamlit)

1. **Open a new terminal** and navigate to frontend directory:
   ```bash
   cd frontend
   ```

2. **Start the Streamlit application**:
   ```bash
   streamlit run app.py
   ```

   The frontend will be available at: `http://localhost:8501`

## 🔧 Development Notes

- The backend runs on **port 8000** with hot reload enabled
- The frontend runs on **port 8501** (default Streamlit port)
- Make sure both services are running simultaneously for full functionality
