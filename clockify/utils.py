from datetime import date, datetime, timedelta


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
