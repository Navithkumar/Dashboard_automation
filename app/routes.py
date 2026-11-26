"""FastAPI HTTP routes, API endpoints, and SSE log streaming."""
import asyncio
import json
import uuid
from pathlib import Path
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from fastapi.responses import HTMLResponse, StreamingResponse, FileResponse
from fastapi.templating import Jinja2Templates

from config.settings import settings
from core.logger import broadcaster, setup_logger
from automation.runner import AutomationRunner
from app.schemas import AutomationRequest, AutomationResponse

router = APIRouter()
templates = Jinja2Templates(directory=str(settings.base_dir / "app" / "templates"))

# In-memory storage for active and completed runs
RUNS_STORE: Dict[str, Dict[str, Any]] = {}
logger = setup_logger("app.routes")


def _execute_automation_task(run_id: str, request_data: AutomationRequest):
    """Worker task executed in background thread."""
    try:
        runner = AutomationRunner(
            url=request_data.url,
            username=request_data.username,
            password=request_data.password,
            first_name=request_data.first_name,
            last_name=request_data.last_name,
            employee_id=request_data.employee_id,
            middle_name=request_data.middle_name,
            headless=request_data.headless,
            run_id=run_id,
        )
        result = runner.execute()
        RUNS_STORE[run_id] = result
        # Broadcast final completion event through the logger broadcaster
        broadcaster.broadcast(
            run_id,
            f"Automation finished with status: {result['status']}",
            level="INFO" if result["status"] == "SUCCESS" else "ERROR",
            step="Complete",
        )
    except Exception as e:
        logger.error(f"Background worker failed for run {run_id}: {e}")
        RUNS_STORE[run_id] = {
            "run_id": run_id,
            "status": "FAILED",
            "error": {"error_type": type(e).__name__, "message": str(e), "step": "Worker"},
        }
        broadcaster.broadcast(
            run_id,
            f"Worker error: {str(e)}",
            level="ERROR",
            step="Worker Error",
        )


@router.get("/", response_class=HTMLResponse)
async def dashboard_view(request: Request):
    """Renders the main dashboard interface."""
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "default_url": settings.orangehrm_url,
            "default_username": settings.default_username,
            "default_password": settings.default_password,
            "default_headless": settings.headless,
        },
    )


@router.post("/api/run-automation")
async def trigger_automation(
    payload: AutomationRequest,
    background_tasks: BackgroundTasks,
):
    """Triggers the OrangeHRM RPA flow asynchronously and returns run_id."""
    run_id = f"run_{uuid.uuid4().hex[:8]}"
    RUNS_STORE[run_id] = {
        "run_id": run_id,
        "status": "PENDING",
        "error": None,
    }

    # Dispatch to background task
    background_tasks.add_task(_execute_automation_task, run_id, payload)
    
    return {
        "status": "ACCEPTED",
        "run_id": run_id,
        "message": "Automation triggered successfully. Stream logs via /api/stream-logs/" + run_id,
    }


@router.get("/api/stream-logs/{run_id}")
async def stream_logs(run_id: str):
    """Streams real-time Server-Sent Events (SSE) logs for the specified run."""
    queue = broadcaster.register(run_id)

    async def event_generator():
        try:
            # Yield initial connection message
            yield f"data: {json.dumps({'timestamp': '', 'level': 'INFO', 'step': 'Connected', 'message': f'Connected to log stream for {run_id}'})}\n\n"

            while True:
                try:
                    # Wait for next log message with timeout for keep-alive
                    log_entry = await asyncio.wait_for(queue.get(), timeout=1.0)
                    yield f"data: {json.dumps(log_entry)}\n\n"
                    
                    # If this is the completion log, check store and send full result payload
                    if log_entry.get("step") in ("Complete", "Worker Error") and run_id in RUNS_STORE:
                        run_info = RUNS_STORE[run_id]
                        if run_info.get("status") in ("SUCCESS", "FAILED"):
                            await asyncio.sleep(0.5)
                            yield f"event: complete\ndata: {json.dumps(run_info)}\n\n"
                            break

                except asyncio.TimeoutError:
                    # Check if run already completed
                    if run_id in RUNS_STORE and RUNS_STORE[run_id].get("status") in ("SUCCESS", "FAILED"):
                        run_info = RUNS_STORE[run_id]
                        yield f"event: complete\ndata: {json.dumps(run_info)}\n\n"
                        break
                    # Send keep-alive ping comment
                    yield ": ping\n\n"

        except asyncio.CancelledError:
            pass
        finally:
            broadcaster.unregister(run_id, queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/api/status/{run_id}")
async def get_run_status(run_id: str):
    """Returns current execution state or completed results of a run."""
    if run_id not in RUNS_STORE:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")
    return RUNS_STORE[run_id]


@router.get("/api/download/{file_type}/{filename}")
async def download_file(file_type: str, filename: str):
    """Safely serves generated CSV or Excel files."""
    if file_type not in ("csv", "excel"):
        raise HTTPException(status_code=400, detail="Invalid file type.")

    # Sanitize filename
    safe_filename = Path(filename).name
    file_path = settings.data_dir / safe_filename

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found.")

    media_type = "text/csv" if file_type == "csv" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    return FileResponse(
        path=str(file_path),
        filename=safe_filename,
        media_type=media_type,
    )


@router.get("/api/runs")
async def list_runs():
    """Lists summary of all executed runs in this session."""
    summaries = []
    for r_id, data in RUNS_STORE.items():
        summaries.append({
            "run_id": r_id,
            "status": data.get("status"),
            "duration": data.get("duration_seconds", 0),
            "inserted_employee": data.get("inserted_employee"),
            "extracted_count": data.get("extracted_count", 0),
        })
    return summaries
