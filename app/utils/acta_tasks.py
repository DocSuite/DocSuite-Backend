import re

from app.schemas.acta import TaskItem

TASK_LINE_PATTERN = re.compile(r"^\s*[-*]\s*\[(?P<done>[ xX])\]\s*(?P<text>.+?)\s*$")


def extract_tasks_from_markdown(content: str) -> list[TaskItem]:
    tasks: list[TaskItem] = []
    in_tasks_section = False

    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("## "):
            in_tasks_section = stripped.lower().startswith("## tareas")
            continue

        if not in_tasks_section:
            continue

        match = TASK_LINE_PATTERN.match(line)
        if match:
            tasks.append(
                TaskItem(
                    description=match.group("text").strip(),
                    done=match.group("done").lower() == "x",
                )
            )

    return tasks
