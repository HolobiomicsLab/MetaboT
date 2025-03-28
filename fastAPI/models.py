from typing import Optional

from pydantic import BaseModel


class WorkflowRequest(BaseModel):
    prompt: Optional[str] = None
    session_id: str
    endpoint_url: Optional[str] = None