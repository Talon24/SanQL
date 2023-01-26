"""Mysql walker"""


def prunejoin(dict_, list_, sep=", "):
    """Remove non-values from list and join it using sep."""
    return sep.join([dict_.get(i) for i in list_ if dict_.get(i)])


def walker(tree, parent=None, depth=0):
    """Walk through the vertica explain plan."""
    current = tree.copy()
    current.pop("nested_loop", None)
    current.pop("duplicates_removal", None)
    current.pop("ordering_operation", None)
    # current.pop("Inner", None)
    # current.pop("Outer", None)
    # current.pop("MATERIALIZE", None)
    # current.pop("MATERIALIZE_AT_OUPUT", None)
    current.pop("used_columns", None)
    for name, cost in current["cost_info"].items():
        current["Cost - {}".format(name)] = cost
    current["__cost"] = sum(float(current["cost_info"][i])
                            for i in current["cost_info"]
                            if i.endswith("cost"))
    # costs = [current.get("Cost - query_cost", None),
    #          current.get("Cost - prefix_cost", None),
    #          current.get("Cost - eval_cost", None),
    #          current.get("Cost - read_cost", None)]
    # current["__cost"] = float(next(c for c in costs if c is not None))
    current.pop("cost_info", None)
    name = current.get("access_type", "")
    if "table_name" in current:
        name += " as {}".format(current["table_name"])
    if depth == 0:
        name += " - Total Cost: {:15,.2f}".format(current["__cost"])
    current["__label"] = name
    current.pop("ordering_operation", None)
    current.pop("duplicates_removal", None)
    yield current, parent, depth
    container = tree
    container = container.get("ordering_operation", container)
    container = container.get("duplicates_removal", container)
    if "nested_loop" in container:
        for entry in container["nested_loop"]:
            yield from walker(entry["table"], current, depth + 1)
    if "optimized_away_subqueries" in container:
        for entry in container["optimized_away_subqueries"]:
            yield from walker(entry["query_block"]["table"], current, depth + 1)
