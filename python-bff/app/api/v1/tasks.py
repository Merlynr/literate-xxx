from __future__ import annotations
from fastapi import APIRouter
from pydantic import BaseModel, Field
from celery.result import AsyncResult
from app.workers.celery_app import celery_app

router = APIRouter()


class PingRequest(BaseModel):
    message: str = Field(default="pong", description="Echo message")


class TaskResponse(BaseModel):
    task_id: str
    status: str


class TaskResultResponse(BaseModel):
    task_id: str
    status: str
    result: dict | None = None


@router.post("/tasks/ping", response_model=TaskResponse)
async def dispatch_ping(req: PingRequest):
    """Dispatch a test ping task to Celery worker."""
    result = celery_app.send_task("ping", kwargs={"message": req.message})
    return TaskResponse(task_id=result.id, status="queued")


@router.get("/tasks/{task_id}", response_model=TaskResultResponse)
async def get_task_result(task_id: str):
    """Poll Celery task result by task_id."""
    result = AsyncResult(task_id, app=celery_app)
    if result.state == "PENDING":
        return TaskResultResponse(task_id=task_id, status="pending", result=None)
    if result.state == "FAILURE":
        return TaskResultResponse(task_id=task_id, status="failed", result={"error": str(result.result)})
    if result.state == "SUCCESS":
        return TaskResultResponse(task_id=task_id, status="succeeded", result=result.result)
    return TaskResultResponse(task_id=task_id, status=result.state.lower(), result=None)
