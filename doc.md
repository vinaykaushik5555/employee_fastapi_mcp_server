HR Assistant & Employee Leave Management System – Detailed Overview

This document expands on the previous overview, adding more visuals and detailing the technologies and libraries used. It is designed to be client‑friendly and highlights how different flows operate within the system.

1. Tech Stack
Layer	Technologies & Libraries
Front‑End	Streamlit – Python web framework for data apps.
	langgraph – builds state‑machine agents on top of LLMs.
	langchain – orchestrates LLM calls and tools.
Middleware	Anyio – async concurrency library for running async tasks
	langchain_mcp_adapters – connectors for calling MCP tools
Back‑End	FastAPI – high‑performance API framework.
	FastMCP – exposes FastAPI endpoints as MCP tools
	SQLAlchemy – ORM for interacting with the database
LLM Providers	OpenAI / GPT‑4 – used for intent classification and data extraction
Other	Pydantic – data validation (schemas, DTOs)
	UUID/Datetime – token generation, date management

These technologies work together to provide a conversational interface for employees and administrators, while ensuring robust business logic and persistent storage.

2. High‑Level Architecture (recap)
graph TD
    User[Admin/Employee] --> UI[HR Assistant UI (Streamlit)]
    UI --> Agent[LangGraph Agent]
    Agent --> Client[MCP Client]
    Client --> Server[MCP Server (FastAPI + FastMCP)]
    Server --> DB[Database (SQLAlchemy)]

3. Detailed Flow Diagrams
3.1 Leave Balance Query

A simple query where an employee checks their current leave balance.

sequenceDiagram
    participant Emp as Employee
    participant UI as HR Assistant UI
    participant Agent
    participant Client as MCP Client
    participant Server as MCP Server

    Emp ->> UI: "What is my leave balance?"
    UI ->> Agent: Send message
    Agent ->> Agent: Classify intent = leave_balance
    Agent ->> Client: mcp_get_leave_balance(token)
    Client ->> Server: get_leave_balance(token)
    Server ->> DB: Fetch LeaveBalance row
    DB -->> Server: Balances
    Server -->> Client: { balances }
    Client -->> Agent: Response
    Agent ->> UI: "Your current leave balance is..."

3.2 Apply for Leave

This flow shows a multi‑turn conversation where an employee applies for leave. The agent gathers required fields, checks for sufficient balance and non‑overlapping dates, and applies the leave.

sequenceDiagram
    participant Emp as Employee
    participant UI as HR Assistant UI
    participant Agent
    participant Client as MCP Client
    participant Server as MCP Server
    participant DB as Database

    Emp ->> UI: "I want to take leave next month"
    UI ->> Agent: Message
    Agent ->> Agent: Classify intent = leave_apply
    Agent ->> Agent: Extract missing fields (type, start_date, end_date, reason)
    Agent ->> UI: Asks clarifying questions
    Emp ->> UI: Provides leave_type, start_date, end_date, reason
    Agent ->> Client: mcp_apply_leave(token, leave_type, days, start_date, reason)
    Client ->> Server: apply_leave(token, leave_type, days, start_date, reason)
    Server ->> DB: Check balance & existing leave for overlaps
    DB -->> Server: Balance & existing requests
    Note right of Server: New business rule prevents overlapping dates
    Server -->> Client: Success or error (insufficient balance/overlap)
    Client -->> Agent: Response
    Agent ->> UI: Notifies employee of result & remaining balance

3.3 Employee Onboarding (Admin Flow)

An HR administrator can onboard a new employee via chat, as described previously. The sequence diagram illustrates how the agent gathers details and calls the server.

sequenceDiagram
    participant Admin as HR Administrator
    participant UI as HR Assistant UI
    participant Agent
    participant Client as MCP Client
    participant Server as MCP Server
    participant DB as Database

    Admin ->> UI: "Onboard a new employee"
    UI ->> Agent: Message
    Agent ->> Agent: Classify intent = employee_onboard
    Agent ->> Agent: Extract ID, username, password, name, email, department
    Agent ->> UI: Prompts for missing fields
    Admin ->> UI: Provides details
    Agent ->> Client: mcp_admin_create_employee(token, id, username, password, name, email, dept)
    Client ->> Server: admin_create_employee(token, ...)
    Server ->> DB: Create Employee & default LeaveBalance
    DB -->> Server: Confirmation
    Server -->> Client: Created employee info
    Client -->> Agent: Response
    Agent ->> UI: "Employee successfully onboarded!"

4. Business Rule Enhancements

Role‑Based Permissions – The admin_create_employee tool is restricted to administrators; non‑admins receive a forbidden error
raw.githubusercontent.com
.

Sufficient Balance Check – Employees cannot request more leave days than available. Balance is deducted upon approval.

No Overlapping Leave Requests – When apply_leave is called, the system checks existing requests to prevent overlapping dates
raw.githubusercontent.com
. If a conflict exists, a BUSINESS_RULE_VIOLATION error is returned.

Dynamic Intent Handling – The agent can now handle employee onboarding by classifying employee_onboard in addition to leave‑related intents and policy queries
raw.githubusercontent.com
.

5. Conclusion

The additional visuals illustrate how different user flows traverse the system, while the tech stack summary highlights the frameworks and libraries that power the solution. Together, these diagrams and descriptions provide a comprehensive understanding of the HR assistant and leave management platform. The system leverages modern Python frameworks (FastAPI, Streamlit), advanced orchestration libraries (LangGraph, FastMCP) and integrates LLMs to provide a conversational interface with strict business logic enforcement.