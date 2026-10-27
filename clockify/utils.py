from datetime import date, datetime, timedelta

from clockify.models import TaskSummary


def parse_date(arg: str | None) -> date:
    """
    Parse a date argument, or return today if None.
    Use -n to subtract n days, +n to add n days, or 01/03/25 format.
    """
    if arg is None:
        return date.today()
    if arg.lstrip("-").isdigit():
        return date.today() - timedelta(days=abs(int(arg)))
    if arg.lstrip("+").isdigit():
        return date.today() + timedelta(days=int(arg))

    for fmt in ("%d/%m/%y", "%d/%m/%Y"):
        try:
            return datetime.strptime(arg, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Unrecognised date format: {arg}")


def summarize_by_task(entries: list[dict]) -> list[TaskSummary]:
    """Sum hours per (description, project), largest first. Running entries are skipped."""
    by_task: dict[tuple[str, str], TaskSummary] = {}
    for e in entries:
        interval = e["timeInterval"]
        if not interval.get("end"):
            continue
        start = datetime.fromisoformat(interval["start"].replace("Z", "+00:00"))
        end = datetime.fromisoformat(interval["end"].replace("Z", "+00:00"))
        key = (e.get("description") or "—", e.get("projectName", "—"))
        task = by_task.setdefault(key, TaskSummary(description=key[0], project_name=key[1], hours=0, entries=0))
        task.hours += (end - start).total_seconds() / 3600
        task.entries += 1
    return sorted(by_task.values(), key=lambda t: t.hours, reverse=True)
