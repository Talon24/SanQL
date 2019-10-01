"""Explainplan as sankey"""

import sys
import json
import argparse
import traceback
import tkinter
import tkinter.scrolledtext
import tkinter.messagebox

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


def generate(data, to_json=False):
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
        arrangement="freeform",
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
                      font_size=12, font_family="monospace")
    if returning:
        return json.dumps([fig], cls=utils.PlotlyJSONEncoder)
    else:
        fig.show()
    return None


class App(tkinter.Tk):
    """Gui that lets user input an explain plan."""

    def __init__(self):
        super().__init__()
        self.report_callback_exception = self.show_error
        self.title("Explain Visualizer")
        tkinter.Label(self, text="Enter explain plan here. Prefixes e.g.\n"
                      "Postgres: explain (format json) \t Vertica: explain json"
                      ).grid(row=0, column=0)
        text = tkinter.scrolledtext.ScrolledText(self)
        text.grid(row=1, column=0, columnspan=3, sticky="NEWS")
        text.focus_set()
        button = tkinter.Button(
            self, text="Analyze", command=self.try_generate)
        button.grid(row=2, column=0, columnspan=3, sticky="NS")
        inputbutton = tkinter.Button(self, text="Load from clipboard",
                                     command=self.load_clipboard)
        inputbutton.grid(row=0, column=1, sticky="E")
        helptext = ("To visualize an SQL query, get the explain plan from the "
                    "database formatted as json (Add a prefix to your query "
                    "that your database can handle.\nFor Postgres, this would "
                    "be `explain (format json)`, for Vertica, it would be "
                    "`explain json`) and load it - preferably using the "
                    "\"Load from clipboard\"-button. This applies some "
                    "preparing to the given string. If you decide to paste "
                    "directly into the text area, avoid having your json be on"
                    " a single line as this will stagger the GUI.\n"
                    "Press the \"Analyze\"-button to view the sankey-diagram "
                    "in a new tab in your webbrowser.")
        tkinter.Button(self, text="?",
                       command=lambda: tkinter.messagebox.showinfo(
                           "Help", helptext)).grid(row=0, column=2, sticky="E")
        self.textarea = text
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.mainloop()

    def show_error(self, etype, value, trace):
        """Called upon exception, shows stacktrace."""
        def write_to_clip(text):
            self.clipboard_clear()
            self.clipboard_append(text)
        err = traceback.format_exception(etype, value, trace)
        errtext = "".join(err)
        # tkinter.messagebox.showerror('Exception', "".join(err))
        messagebox = tkinter.Toplevel(self)
        messagebox.title = "Error!"
        messagebox.columnconfigure(0, weight=1)
        messagebox.rowconfigure(1, weight=1)
        tkinter.Label(messagebox,
                      text="An error occurred!").grid(row=0, column=0)
        text = tkinter.Text(messagebox)
        text.insert("insert", errtext)
        text.config(state=tkinter.DISABLED)
        text.grid(row=1, column=0, columnspan=2, sticky="news")
        tkinter.Button(messagebox, command=lambda: write_to_clip(errtext),
                       text="Copy trace").grid(row=0, column=1)

    def try_generate(self):
        """Generate diagram if input is valid json."""
        text = self.textarea.get("1.0", tkinter.END)
        try:
            data = json.loads(text)
        except json.decoder.JSONDecodeError:
            tkinter.messagebox.showerror(
                "Invalid input",
                "Given input is not a json-formatted explain plan")
        else:
            generate(data)

    def load_clipboard(self):
        """Load text from clipboard and prepare string."""
        try:
            text = self.clipboard_get()
        except tkinter.TclError:
            return
        text = find_json("".join(text))
        try:
            text = json.dumps(json.loads(text), indent=4)
            # Text widget is slow with long unbroken text
        except json.decoder.JSONDecodeError:
            pass
        self.textarea.delete(1.0, tkinter.END)
        self.textarea.insert(1.0, text)


def main():
    """main"""
    parser = argparse.ArgumentParser()
    parser.add_argument("file", help="Execution plan json file.", nargs="?")
    parser.add_argument("-m", "--mode", default="gui", help="Specify how to "
                        "pass explain plan to program. Default: GUI.",
                        choices=["file", "stdin", "input", "gui"])
    arguments = parser.parse_args()
    lines = []
    if arguments.mode == "gui":
        App()
        exit()
    elif arguments.mode == "input":
        try:
            print("Enter SQL Execution plan. Interrupt [CTRL + C] or "
                  "add EoT char [CTRL + D] to finish.")
            while True:
                new = input()
                lines.append(new.replace("\x04", ""))
                if new.endswith("\x04"):
                    break
        except KeyboardInterrupt:
            pass
        data = "\n".join(lines)
        data = json.loads(data)
        generate(data)
    elif arguments.mode == "stdin":
        data = json.loads(sys.stdin.read())
        generate(data)
    elif arguments.mode == "file":
        with open(arguments.file) as file:
            data = json.load(file)
        generate(data)


if __name__ == '__main__':
    main()
