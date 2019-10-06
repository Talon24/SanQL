"""Explainplan as sankey"""

import sys
import json

try:
    import terminaltables
except ImportError:
    pass
# import plotly.graph_objects as go
from plotly.graph_objects import Figure
from plotly.graph_objects import Sankey
from plotly import utils

from walkers.postgres import walker as pg_walker
from walkers.vertica import walker as vert_walker


def walker(tree):
    """Walker interface."""
    if isinstance(tree, list):
        source = "postgres"
    else:
        source = "vertica"
    if source == "postgres":
        yield from pg_walker(tree[0]["Plan"])
    elif source == "vertica":
        yield from vert_walker(tree)


def prettify_details(data):
    """Make data more readable."""
    new = []
    if "terminaltables" in sys.modules:
        for key, value in data.items():
            if key.startswith("__"):
                continue
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                new.append((key, "{:15,.2f}".format(value)))
            else:
                new.append((key, value))
        table = terminaltables.DoubleTable(new)
        table.inner_heading_row_border = False
        table.justify_columns[1] = 'right'
        return table.table.replace("\n", "<br />")
    else:
        formatted = json.dumps({k: v for k, v in data.items()
                                if not k.startswith("__")}, indent=4)
        new = formatted[2:-2].replace("\n", "<br />")
    return new


def find_json(data):
    """Find the json if explain plan contains surrounding information."""
    if data.startswith("------------------------------ \n"
                       "QUERY PLAN DESCRIPTION: \n"
                       "------------------------------"):
        # Vertica-like
        data = data.split("JSON format:\n")[1].split("End JSON format")[0]
    return data


def generate(data, to_json=False, mode="freeform"):
    """Generate graph data and show in browser."""
    labels, source, target, value, hovers = [], [], [], [], []
    indexes = {}
    indexes[json.dumps(None)] = 0
    labels.append("")
    # data = find_json(data)
    for idx, (thing, parent, _) in enumerate(walker(data), 1):
        indexes[json.dumps(thing)] = idx
        label = ("{}".format(thing.get("__label", "Unknown")))
        labels.append(label)
        source.append(idx)
        target.append(indexes[json.dumps(parent)])
        value.append(max((thing["__cost"], 0.00001)))  # 0.0 wouldn't plot
        hovers.append(prettify_details(thing))

    fig = Figure(data=[Sankey(
        ids=labels,
        arrangement=mode,
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=labels,
            color=["green"] + ["blue"] * (len(labels) - 1),
        ),
        link=dict(
            source=source,
            target=target,
            value=value,
            label=hovers,
            hoverlabel=dict(font=dict(
                family="Courier New, monospace"))
        )
    )])

    fig.update_layout(title_text="Execution plan",
                      margin=dict(l=0, r=0, t=0, b=0),
                      font_size=12, font_family="monospace")
    if to_json:
        return json.dumps([fig], cls=utils.PlotlyJSONEncoder)
    else:
        fig.show()
    return None
