# Leave Management System – FastAPI + SQLite + BasicAuth + MCP

A simple Leave Management System built using **FastAPI**, **SQLite**, **Basic Authentication**, and **FastMCP**.  
Supports employee management, leave balance administration, and leave request tracking.

---

## 🚀 Features

- Create employees
- **Basic Authentication** using `username:password`
- **Apply**, **credit**, and **check** leave balances
- View employee leave request history
- **SQLite database**
- **FastMCP server mode**
- Clean modular architecture
- CORS enabled

---

## 📦 Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | FastAPI |
| Authentication | HTTP Basic Auth (plain text comparison) |
| Database | SQLite + SQLAlchemy ORM |
| Automation / MCP | FastMCP |
| Application Server | Uvicorn |

---

## 🛠 Setup Instructions

### 1. Install dependencies
```bash
uv pip install -r requirements.txt

## 📍 API Documentation (Swagger & ReDoc)

Once the server is running, you can access the built-in documentation at:

### **Swagger UI**
http://127.0.0.1:8000/docs

### **ReDoc**
http://127.0.0.1:8000/redoc

---

## 🧠 Running MCP Server (FastMCP)

This project supports **MCP Mode**, allowing tools and automation integrations.

### Run API
```bash
uv run uvicorn main:app --reload

### Run MCP Interceptor
```bash
uv run fastmcp dev main.p