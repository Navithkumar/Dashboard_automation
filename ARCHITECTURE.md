# Architecture & Technical Design Specification

## 1. System Overview

The **OrangeHRM RPA Dashboard Automation** platform is an enterprise-grade automation system that bridges a modern, reactive web control center with an automated browser bot. It replaces brittle, one-off automation scripts with a structured, decoupled architecture adhering to SOLID design principles.

```
       +-------------------------------------------------------------+
       |                     User Web Browser                        |
       |  (HTML5 / Tailwind / Vanilla JS / Server-Sent Events [SSE]) |
       +------------------------------+------------------------------+
                                      |
                         REST / SSE   | HTTP Requests
                                      v
       +-------------------------------------------------------------+
       |                     FastAPI Web Server                      |
       |  - app.main (Static mounts, CORS, App Lifecycle)            |
       |  - app.routes (REST endpoints, SSE Streamer, File Server)    |
       |  - app.schemas (Pydantic payload validation)                |
       +------------------------------+------------------------------+
                                      |
                     Background Task  | Dispatch (Threadpool)
                                      v
       +-------------------------------------------------------------+
       |                 automation.runner (Orchestrator)            |
       +-------+----------------------+----------------------+-------+
               |                      |                      |
               v                      v                      v
        +--------------+      +---------------+      +---------------+
        |  LoginPage   |      | DashboardPage |      |    PimPage    |
        +-------+------+      +-------+-------+      +-------+-------+
                |                     |                      |
                +---------------------+----------------------+
                                      |
                                      v
                       +------------------------------+
                       |   Playwright Browser Engine  |
                       |       (Google Chrome)        |
                       +--------------+---------------+
                                      |
                                      v
                       +------------------------------+
                       |    OrangeHRM Cloud Instance  |
                       +------------------------------+
```

---

## 2. Design Patterns & Principles

### A. Page Object Model (POM)
The automation layer strictly adheres to the Page Object Model design pattern:
- **`BasePage`** (`automation/pages/base_page.py`): Encapsulates core browser actions, resilient wait strategies, and automated timestamped screenshot captures.
- **`LoginPage`** (`automation/pages/login_page.py`): Encapsulates authentication input fields, submission, and validation alerting.
- **`DashboardPage`** (`automation/pages/dashboard_page.py`): Handles top-level navigation, sidebar module links, and user dropdown logout.
- **`PimPage`** (`automation/pages/pim_page.py`): Encapsulates employee creation forms, toast verification, personal details redirect verification, and table scraping.

**Benefits**:
- Decouples tests and orchestration logic from underlying DOM selectors.
- OrangeHRM UI modifications only require selector updates in a single page class.

### B. Reactive Asynchronous Log Streaming (SSE)
Rather than blocking the HTTP request or polling the server repeatedly:
1. The frontend initiates automation via `POST /api/run-automation`.
2. The server responds immediately with an accepted status and unique `run_id`, dispatching the automation into an async background thread.
3. The frontend establishes an EventSource connection to `/api/stream-logs/{run_id}`.
4. As each automation step executes, the `RunLogger` broadcasts log events to the `LogBroadcaster` hub.
5. The frontend receives real-time JSON log frames and updates the UI timeline and terminal log console instantly.
6. Upon completion, an `event: complete` SSE packet delivers the full result payload (inserted employee, extracted count, file links, and screenshot names).

### C. Strong Domain Exception Hierarchy
Failures during RPA automation are captured and mapped into clear, contextual exceptions:
- `AutomationError` (Root base exception with `.step` and `.details` attributes)
  - `AuthenticationError` (Login failures or bad credentials)
  - `NavigationError` (Page load timeouts or missing navigation elements)
  - `EmployeeCreationError` (Form validation or verification timeouts)
  - `DataExtractionError` (Table parsing issues)

---

## 3. Storage & Artifact Management

```
outputs/
├── data/              # Stores generated CSV and Excel records per run
├── logs/              # Rotating timestamped log files
└── screenshots/       # Visual audit trail for every execution step
```

When runs complete, the `export_employee_data` utility generates both:
- **CSV format**: UTF-8 encoded text for data pipelines.
- **Excel format (.xlsx)**: Formatted Microsoft Excel workbook via `openpyxl`.
