import yaml
from pathlib import Path
from typing import List
from src.domain.todo_model import TodoItem

TODO_FILE = Path(__file__).parent.parent / "data" / "todos.yaml"

def load_todos() -> List[TodoItem]:
    if not TODO_FILE.exists():
        return []
    with open(TODO_FILE, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or []
    return [TodoItem(**item) for item in data]

def save_todos(todos: List[TodoItem]) -> None:
    TODO_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(TODO_FILE, "w", encoding="utf-8") as f:
        yaml.safe_dump([todo.model_dump() for todo in todos], f, allow_unicode=True) 