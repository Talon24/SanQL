"""Mysql walker"""


def prunejoin(dict_, list_, sep=", "):
    """Remove non-values from list and join it using sep."""
    return sep.join([dict_.get(i) for i in list_ if dict_.get(i)])


def walker(tree, parent=None, depth=0):
    """Walk through the vertica explain plan."""
    current = tree.copy()
    current.pop("nested_loop", None)
    # current.pop("Inner", None)
    # current.pop("Outer", None)
    # current.pop("MATERIALIZE", None)
    # current.pop("MATERIALIZE_AT_OUPUT", None)
    current.pop("used_columns", None)
    for name, cost in current["cost_info"].items():
        current["Cost - {}".format(name)] = cost
    current["__cost"] = sum([float(current["cost_info"][i])
                             for i in current["cost_info"]
                             if i.endswith("cost")])
    # costs = [current.get("Cost - query_cost", None),
    #          current.get("Cost - prefix_cost", None),
    #          current.get("Cost - eval_cost", None),
    #          current.get("Cost - read_cost", None)]
    # current["__cost"] = float(next(c for c in costs if c is not None))
    current.pop("cost_info", None)
    name = prunejoin(current, ["table_name"], sep=" ")
    if depth == 0:
        name += " - Total Cost: {:15,.2f}".format(current["__cost"])
    current["__label"] = name
    yield current, parent, depth
    if "nested_loop" in tree:
        for entry in tree["nested_loop"]:
            yield from walker(entry["table"], current, depth + 1)
