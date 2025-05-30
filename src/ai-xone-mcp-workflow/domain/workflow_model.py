from enum import Enum
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

class WorkflowStatus(str, Enum):
    active = "active"         # 启用
    inactive = "inactive"     # 停用
    archived = "archived"     # 已归档/删除

class Step(BaseModel):
    name: str
    order: int
    context: Optional[str] = None      # 上下文，背景信息、约束、场景说明
    instruction: str                   # 指令，明确要执行的操作
    input: Optional[str] = None        # 输入，模型需要处理的数据
    output: Optional[str] = None       # 输出，期望的返回格式或结构
    params: Optional[Dict[str, Any]] = None  # 其他参数（可选）

class Workflow(BaseModel):
    id: Optional[str] = None  # 唯一标识
    name: str
    steps: List[Step]
    status: WorkflowStatus = WorkflowStatus.active
    description: Optional[str] = None
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()