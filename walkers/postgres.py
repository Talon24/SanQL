"""Postgres walker"""


def timeformat(millisec):
    """format a timedelta"""
    secs = millisec / 1000
    hours = int(secs / 60 / 60)
    mins = int(secs / 60)
    secs = secs % 60
    out = "{:02}:{:02}:{:05.2f}".format(hours, mins, secs)
    return out


def sizeformat(num, suffix='B'):
    """Format bytes as human readable size."""
    for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
        if abs(num) < 1024.0:
            return "%3.1f %s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f %s%s" % (num, 'Yi', suffix)


def walker(tree, parent=None, depth=0):
    """Walk through the postgres explain plan."""
    current = tree.copy()
    current.pop("Plans", None)
    if "Actual Total Time" in current:
        current["__cost"] = current["Actual Total Time"]
    else:
        current["__cost"] = current["Total Cost"]
    # Build name
    name = current["Node Type"]
    if name == "CTE Scan" and "CTE Name" in current:
        name += " as {}".format(current["CTE Name"])
    elif "Alias" in current:
        name += " as {}".format(current["Alias"])
    elif "Subplan Name" in current:
        name += " for {}".format(current["Subplan Name"])
    if depth == 0:
        name += " - Total Cost: {:15,.2f}".format(current["__cost"])
    current["__label"] = name

    for entry in [e for e in current if "Time" in e]:
        current[entry] = timeformat(current[entry])
    for entry in [e for e in current if "Space Used" in e]:
        space = current[entry]  # Postgres returns space in KB
        current[entry] = "{} KiB".format(space)
        if space >= 1024:
            current[entry] += " - Approx. {}".format(sizeformat(space*1000))

    yield current, parent, depth
    if "Plans" in tree:
        # for plan in sorted(tree["Plans"], key=lambda x: x["Total Cost"], reverse=True):
        for plan in tree["Plans"]:
            yield from walker(plan, current, depth + 1)
