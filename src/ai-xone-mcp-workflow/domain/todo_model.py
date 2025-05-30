from enum import Enum
from pydantic import BaseModel
from typing import Optional

class TodoStatus(str, Enum):
    pending = "pending"         # 待办
    in_progress = "in_progress" # 进行中
    completed = "completed"     # 已完成
    archived = "archived"       # 已归档/取消

class TodoItem(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    workflow_id: Optional[str] = None
    status: TodoStatus = TodoStatus.pending 