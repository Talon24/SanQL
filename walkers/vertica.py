"""Vertica walker"""


def prunejoin(dict_, list_, sep=", "):
    """Remove non-values from list and join it using sep."""
    return sep.join([dict_.get(i) for i in list_ if dict_.get(i)])


def walker(tree, parent=None, depth=0):
    """Walk through the vertica explain plan."""
    current = tree.copy()
    current.pop("INPUT", None)
    current.pop("Inner", None)
    current.pop("Outer", None)
    current.pop("MATERIALIZE", None)
    current.pop("MATERIALIZE_AT_OUPUT", None)
    current["__cost"] = current["COST"]
    name = prunejoin(current, ["PATH_NAME", "EXTRA"], sep=" ")
    current["__label"] = name
    yield current, parent, depth
    if "INPUT" in tree:
        yield from walker(tree["INPUT"], current, depth + 1)
    if "Inner" in tree:
        yield from walker(tree["Inner"], current, depth + 1)
    if "Outer" in tree:
        yield from walker(tree["Outer"], current, depth + 1)
