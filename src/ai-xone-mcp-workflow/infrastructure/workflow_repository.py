import yaml
from pathlib import Path
from typing import List, Optional
from src.domain.workflow_model import Workflow, Step

WORKFLOW_FILE = Path(__file__).parent.parent / "data" / "workflows.yaml"

def load_workflows(random_string: Optional[str] = None) -> List[Workflow]:
    if not WORKFLOW_FILE.exists():
        return []
    try:
        with open(WORKFLOW_FILE, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or []
        # 兼容 Step 结构体
        workflows = []
        for item in data:
            if 'steps' in item and isinstance(item['steps'], list):
                item['steps'] = [Step(**step) if not isinstance(step, Step) else step for step in item['steps']]
            workflows.append(Workflow(**item))
        return workflows
    except Exception:
        return []

def save_workflows(workflows: List[Workflow]) -> None:
    WORKFLOW_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(WORKFLOW_FILE, "w", encoding="utf-8") as f:
        yaml.safe_dump([wf.model_dump(mode='json') for wf in workflows], f, allow_unicode=True) 