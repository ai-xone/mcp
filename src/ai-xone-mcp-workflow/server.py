from fastmcp import FastMCP
import asyncio
import logging
from typing import List, Optional, Dict, Any
from src.domain.todo_model import TodoItem
from src.domain.workflow_model import Workflow, Step, WorkflowStatus
from src.infrastructure.todo_repository import load_todos, save_todos
from src.infrastructure.workflow_repository import load_workflows, save_workflows
import uuid
from datetime import datetime

# 移除已存在的 root logger handler
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

# 设置日志格式
logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s [%(levelname)s] %(filename)s:%(lineno)d %(message)s'
)
# 控制第三方库日志
logging.getLogger("uvicorn").setLevel(logging.ERROR)
logging.getLogger("uvicorn.error").setLevel(logging.ERROR)
logging.getLogger("uvicorn.access").setLevel(logging.ERROR)

mcp = FastMCP("FastMCP Demo Server")


@mcp.tool()
def workflow_list(random_string: Optional[str] = None) -> List[Workflow]:
    """
    获取所有已保存的工作流列表。

    Args:
        random_string: 兼容参数（可忽略，通常无需传递）

    Returns:
        List[Workflow]: 当前系统中所有已保存的工作流对象列表。
    """
    return load_workflows(random_string)

@mcp.tool()
def workflow_add(workflow: Workflow) -> Dict[str, Any]:
    """
    添加一个新的工作流。

    Args:
        workflow: Workflow 领域模型对象，包含如下结构：
            - name: 工作流名称
            - steps: List[Step]，每个步骤包含：
                - name: 步骤名称
                - order: 步骤顺序
                - context: 上下文，提供背景信息、约束、场景说明，帮助模型理解任务目标
                - instruction: 指令，明确需要模型执行的具体操作
                - input: 输入，模型需要处理的具体数据或信息
                - output: 输出，规定模型返回结果的格式或结构
                - params: 其他参数（可选）
            - status: WorkflowStatus，工作流状态（active/inactive/archived）
            - description: 工作流描述
            - created_at: 创建时间
            - updated_at: 更新时间

    Returns:
        dict: 新增工作流的详细内容和操作结果。
    """
    workflows = load_workflows()
    workflow_id = str(uuid.uuid4())
    workflow_dict = workflow.model_dump(mode='json')
    workflow_dict['id'] = workflow_id
    new_workflow = Workflow(**workflow_dict)
    workflows.append(new_workflow)
    save_workflows(workflows)
    return {"workflow": new_workflow.model_dump(mode='json'), "result": "success"}

@mcp.tool()
def workflow_update(workflow: Workflow) -> Dict[str, Any]:
    """更新 workflow"""
    workflows = load_workflows()
    found = False
    for idx, wf in enumerate(workflows):
        if wf.id == workflow.id:
            # 保持created_at不变，更新updated_at
            updated_workflow_dict = workflow.model_dump(mode='json')
            updated_workflow_dict['created_at'] = wf.created_at
            updated_workflow_dict['updated_at'] = str(datetime.now())
            workflows[idx] = Workflow(**updated_workflow_dict)
            found = True
            break
    if found:
        save_workflows(workflows)
        return {"workflow": workflows[idx].model_dump(mode='json'), "result": "updated"}
    else:
        return {"workflow": workflow.model_dump(mode='json'), "result": "not_found"}

@mcp.tool()
def workflow_delete(workflow_id: str) -> Dict[str, Any]:
    """删除 workflow"""
    workflows = load_workflows()
    initial_count = len(workflows)
    workflows = [wf for wf in workflows if wf.id != workflow_id]
    if len(workflows) == initial_count:
        return {"workflow_id": workflow_id, "result": "not_found"}
    save_workflows(workflows)
    return {"workflow_id": workflow_id, "result": "deleted"}

@mcp.tool()
def workflow_run(
    workflow_id: Optional[str] = None,
    workflow_name: Optional[str] = None,
    input: Optional[str] = None,
    params: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    工作流调度：支持通过工作流名称或id查找，获取当前步骤指令。
    Args:
        workflow_id: 工作流唯一标识（可选）
        workflow_name: 工作流名称（可选，优先）
        params: 其他上下文参数
    Returns:
        dict: 当前步骤的指令描述
    """
    workflows = load_workflows()
    workflow = None

    # 优先通过名称查找
    if workflow_name:
        # 忽略大小写并只要包含即可
        matches = [wf for wf in workflows if workflow_name.lower() in wf.name.lower()]
        if len(matches) == 1:
            workflow = matches[0]
        elif len(matches) > 1:
            return {
                "status": "ambiguous",
                "message": f"存在多个名称包含'{workflow_name}'的工作流，请指定id。",
                "candidates": [wf.id for wf in matches]
            }
        else:
            return {"status": "not_found", "message": f"未找到名称包含'{workflow_name}'的工作流"}
    elif workflow_id:
        workflow = next((wf for wf in workflows if wf.id == workflow_id), None)
        if not workflow:
            return {"status": "not_found", "message": f"未找到id为{workflow_id}的工作流"}
    else:
        return {
            "status": "error",
            "message": f"未找到匹配的工作流，请指定工作流。",
            "candidates": [wf.name for wf in workflows]
        }

    # 获取当前步骤序号，默认第一个
    current_order = 1
    if params and "current_order" in params:
        current_order = params["current_order"]

    steps_sorted = sorted(workflow.steps, key=lambda s: s.order)
    current_step = next((s for s in steps_sorted if s.order == current_order), None)
    if not current_step:
        return {
            "workflow_id": workflow.id,
            "status": "finished",
            "message": "工作流已全部执行完毕"
        }

    # 指导大模型如何继续执行后续步骤
    continue_instruction = (
        f"每个步骤的执行如果没有说明需要人工确认的都自动执行并输出执行结果。执行完本步骤后，如不需人工确认则自动调用下个步骤，如果需要人工确认则人工确认后调用下个步骤。调用下个步骤的方法： workflow_run，参数 current_order={current_order+1}，以推进到下一个步骤。"
        if current_order < len(steps_sorted) else "本步骤为最后一步，执行完毕后无需继续。"
    )

    # 拼接input，确保None安全
    step_input = (current_step.input or "") + ("\n" + input if input else "")

    instruction_payload = {
        "workflow_id": workflow.id,
        "workflow_name": workflow.name,
        "step_order": current_step.order,
        "step_name": current_step.name,
        "context": current_step.context,
        "instruction": current_step.instruction,
        "input": step_input,
        "output": current_step.output,
        "params": current_step.params,
        "workflow_description": workflow.description,
        "steps_total": len(steps_sorted),
        "continue_instruction": continue_instruction
    }

    return {
        "status": "running",
        "current_step": instruction_payload
    }

if __name__ == '__main__':
    """Run the MCP server with CLI argument support."""
    mcp.run()