"""Desktop App for sql_sankey.

Launches a tkinter application for plan input,
then shows the diagram in the browser.
"""

import sys
import json
import tkinter
import argparse
import traceback

import sql_sankey


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
        """Show window with stack tracke. Called upon error."""
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
            sql_sankey.generate(data)

    def load_clipboard(self):
        """Load text from clipboard and prepare string."""
        try:
            text = self.clipboard_get()
        except tkinter.TclError:
            return
        text = sql_sankey.find_json("".join(text))
        try:
            text = json.dumps(json.loads(text), indent=4)
            # Text widget is slow with long unbroken text
        except json.decoder.JSONDecodeError:
            pass
        self.textarea.delete(1.0, tkinter.END)
        self.textarea.insert(1.0, text)


def main():
    """Argument parsing."""
    parser = argparse.ArgumentParser()
    parser.add_argument("file", help="Execution plan json file.", nargs="?")
    parser.add_argument("-m", "--mode", default="gui", help="Specify how to "
                        "pass explain plan to program. Default: GUI.",
                        choices=["file", "stdin", "input", "gui"])
    arguments = parser.parse_args()
    lines = []
    if arguments.mode == "gui":
        App()
        sys.exit()
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
        sql_sankey.generate(data)
    elif arguments.mode == "stdin":
        data = json.loads(sys.stdin.read())
        sql_sankey.generate(data)
    elif arguments.mode == "file":
        with open(arguments.file) as file:
            data = json.load(file)
        sql_sankey.generate(data)


if __name__ == '__main__':
    main()
