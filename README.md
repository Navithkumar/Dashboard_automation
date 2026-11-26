# OrangeHRM RPA Dashboard-Driven Automation

> **Production-Scale Robotic Process Automation (RPA) Web Dashboard & Automation Suite for OrangeHRM**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com)
[![Playwright](https://img.shields.io/badge/Playwright-1.45+-2EAD33.svg)](https://playwright.dev)
[![Tests Passing](https://img.shields.io/badge/tests-8%20passed-brightgreen.svg)]()

---

## 📋 Table of Contents
- [Project Overview](#-project-overview)
- [Key Features](#-key-features)
- [Architecture & Tech Stack](#-architecture--tech-stack)
- [Project Directory Layout](#-project-directory-layout)
- [Quick Start Guide](#-quick-start-guide)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Launching the Dashboard](#launching-the-dashboard)
  - [Running via CLI](#running-via-cli)
- [Dashboard Walkthrough & Workflow](#-dashboard-walkthrough--workflow)
- [API Reference](#-api-reference)
- [Deliverables Checklist](#-deliverables-checklist)
- [Running Automated Tests](#-running-automated-tests)

---

## 🎯 Project Overview

This project satisfies all requirements for the **RPA Practical Assignment – Dashboard-Driven Automation**:
- **Target Application**: [OrangeHRM Demo Portal](https://opensource-demo.orangehrmlive.com)
- **Primary Objective**: Provide an interactive web dashboard where an operator enters credentials and employee details. All authentication, employee onboarding, verification, tabular data extraction, and logout actions on OrangeHRM are triggered and controlled directly from this dashboard.
- **Deliverables**: Source code, dashboard UI, automation engine, step screenshots, before/after dashboard captures, and exported employee data in both CSV and Excel formats.

---

## ✨ Key Features

1. **Dashboard-Driven Control**:
   - Modern, responsive, dark-mode web dashboard (HTML5, Tailwind CSS, Vanilla JS).
   - Dynamic credential inputs (Username, Password) & Employee fields (First Name, Middle Name, Last Name, Employee ID).
   - One-click ID randomizer to guarantee collision-free test IDs against demo environments.
   - Headless / Headed browser execution toggle.

2. **Enterprise Automation Architecture**:
   - Built on the **Page Object Model (POM)** pattern for clean separation of concerns and maintainability.
   - High-performance browser engine (Playwright with native Chrome) handling dynamic Vue/Angular single-page app (SPA) states and hydration seamlessly.
   - Robust explicit waits and custom error hierarchy (`AuthenticationError`, `NavigationError`, `EmployeeCreationError`, `DataExtractionError`).

3. **Real-time Observability**:
   - **Server-Sent Events (SSE)** log streaming directly into an embedded dashboard console.
   - 7-step visual pipeline indicator (Open Portal → Authenticate → Navigate PIM → Add Employee → Verify Success → Extract Records → Clean Logout).
   - Step-by-step screenshot auditing saved automatically to `outputs/screenshots/`.

4. **Automated Verification & Data Exports**:
   - Validates employee creation via toast alerts and redirection to Personal Details.
   - Displays confirmed employee record on the dashboard.
   - Extracts employee list into a searchable, client-side paginated table.
   - Generates and provides one-click downloads for both **CSV** and **Excel (.xlsx)** formats.

---

## 🏗️ Architecture & Tech Stack

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Backend API** | FastAPI / Uvicorn | Asynchronous web framework, background worker dispatch, SSE streaming |
| **Frontend** | HTML5, Tailwind CSS, Vanilla JS | Interactive, responsive UI with zero heavy build steps |
| **Automation** | Python Playwright & Chrome | SPA-aware browser automation, auto-waiting, DOM interaction |
| **Data Processing** | Pandas, OpenPyXL | Tabular data extraction, CSV formatting, Excel workbook generation |
| **Configuration** | Pydantic Settings, Python-dotenv | Typed, non-hardcoded configuration management |
| **Testing** | Pytest, FastAPI TestClient | Automated integration and regression test suite |

---

## 📂 Project Directory Layout

```
Dashboard_Automation/
├── .env.example                       # Environment variables template
├── .gitignore                         # Git exclusion rules
├── ARCHITECTURE.md                    # Technical design specification
├── README.md                          # Project documentation
├── requirements.txt                   # Dependency manifest
├── run.py                             # Server entrypoint launcher
│
├── config/                            # Application configuration
│   ├── __init__.py
│   └── settings.py                    # Pydantic BaseSettings class
│
├── core/                              # Shared foundation
│   ├── __init__.py
│   ├── exceptions.py                  # Domain-specific automation exceptions
│   └── logger.py                      # Multi-channel logger & SSE broadcaster
│
├── automation/                        # Page Object Model automation engine
│   ├── __init__.py
│   ├── runner.py                      # End-to-end orchestration runner & CLI
│   ├── pages/                         # POM page classes
│   │   ├── __init__.py
│   │   ├── base_page.py               # Shared browser actions & screenshots
│   │   ├── login_page.py              # Login view & authentication checks
│   │   ├── dashboard_page.py          # Dashboard landing & logout dropdown
│   │   └── pim_page.py                # Add employee, verification & data extraction
│   └── utils/
│       ├── __init__.py
│       └── exporter.py                # CSV and Excel export utilities
│
├── app/                               # FastAPI web application
│   ├── __init__.py
│   ├── main.py                        # FastAPI instance & static file mounts
│   ├── routes.py                      # REST endpoints & SSE streaming handlers
│   ├── schemas.py                     # Pydantic request/response schemas
│   ├── static/                        # Static assets
│   │   ├── css/style.css              # Custom styles & animations
│   │   └── js/app.js                  # Frontend controller & SSE receiver
│   └── templates/
│       └── index.html                 # Main dashboard interface
│
├── deliverables/                      # PDF Assignment deliverables
│   ├── data/                          # Extracted CSV and Excel files
│   │   ├── extracted_employees.csv
│   │   └── extracted_employees.xlsx
│   └── screenshots/                   # Dashboard before/after captures
│       ├── dashboard_before_execution.png
│       └── dashboard_after_execution.png
│
├── outputs/                           # Runtime generated artifacts
│   ├── data/                          # Timestamped data exports
│   ├── logs/                          # Execution log files
│   └── screenshots/                   # Step-by-step visual proofs
│
└── tests/                             # Automated test suite
    ├── __init__.py
    └── test_automation.py             # Integration & unit tests
```

---

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.10+ installed
- Google Chrome or Chromium browser installed

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd Dashboard_Automation
   ```

2. **Create and activate a virtual environment** (recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Verify Playwright browser configuration**:
   ```bash
   playwright install chromium
   ```

---

### Launching the Dashboard

Start the application with:
```bash
python3 run.py --port 8000
```

- **Web Dashboard**: [http://localhost:8000](http://localhost:8000)
- **Interactive Swagger API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

### Running via CLI

You can also run the automation suite directly from the command line without the web dashboard:
```bash
python3 -m automation.runner \
  --first-name Alexander \
  --last-name Sterling \
  --emp-id EMP1092 \
  --headless
```

---

## 🖥️ Dashboard Walkthrough & Workflow

1. **Open the Dashboard**: Navigate to `http://localhost:8000`.
2. **Review Credentials**: Default credentials (`Admin` / `admin123`) and URL are pre-populated from settings, or enter custom credentials.
3. **Enter Employee Details**: Enter First Name, Middle Name (optional), Last Name, and Employee ID. Use **Randomize** to generate an ID automatically.
4. **Select Mode**: Leave **Headless Execution** checked for background speed, or uncheck it to watch the Chrome browser execute in real-time.
5. **Click "Trigger Automation"**:
   - The 7-step pipeline cards will light up dynamically as each stage progresses.
   - Real-time step logs will stream into the embedded console.
6. **View Results**:
   - The **Inserted Employee Verified** card displays the confirmed record.
   - The **Extracted Deliverables** card enables downloading **CSV** and **Excel** files.
   - The **Extracted OrangeHRM Employee Data** table displays all scraped records with real-time text search.
   - The **Execution Proof & Screenshots** gallery allows clicking any thumbnail to inspect high-resolution step captures.

---

## 📡 API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | Web dashboard user interface |
| `POST` | `/api/run-automation` | Trigger background automation run |
| `GET` | `/api/stream-logs/{run_id}` | Real-time Server-Sent Events (SSE) log stream |
| `GET` | `/api/status/{run_id}` | Query current execution status & results |
| `GET` | `/api/download/{type}/{file}` | Download exported CSV or Excel files |
| `GET` | `/api/runs` | List summary of all session runs |

---

## 📦 Deliverables Checklist

As specified in the assignment PDF:
- [x] **Source code**: Clean, production-scale modular architecture following POM.
- [x] **Dashboard UI files**: HTML5/CSS3/Tailwind/Vanilla JS in `app/`.
- [x] **Automation script**: Modular Page Object Model in `automation/`.
- [x] **Screenshots of dashboard before and after execution**:
  - `deliverables/screenshots/dashboard_before_execution.png`
  - `deliverables/screenshots/dashboard_after_execution.png`
- [x] **CSV/Excel file of extracted data**:
  - `deliverables/data/extracted_employees.csv`
  - `deliverables/data/extracted_employees.xlsx`
- [x] **Step logs & Screenshots**:
  - Log file in `outputs/logs/`
  - 11 step screenshots in `outputs/screenshots/`

---

## 🧪 Running Automated Tests

Run the full pytest suite to verify all API routes, settings, exports, and exception hierarchies:

```bash
pytest tests/ -v
```

All 8 automated tests validate endpoints, validation constraints, data exporter integrity, and domain exceptions.
