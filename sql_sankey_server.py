"""Start a server"""

import json

from flask import Flask
from flask import render_template
from flask import request

import sql_sankey

app = Flask(__name__)  # pylint: disable=invalid-name


@app.route("/", methods=["GET"])
def welcome_page():
    """Welcome page"""
    return render_template("welcome.html")


@app.route("/", methods=["POST"])
def sankey_page():
    """Attempt to make the diagram, go back if impossible."""
    data = request.form["Query"]
    retrieved = data
    try:
        data = json.loads(data)
    except json.decoder.JSONDecodeError:
        return render_template(
            "welcome.html", errors=["Invalid json!"], data=retrieved)
    try:
        graph_json = sql_sankey.generate(data, to_json=True)
    except KeyError:
        return render_template(
            "welcome.html", errors=["Explain plan flavour is not supported!"],
            data=retrieved)
    return render_template(
        'diagram.html',
        ids=["Graph"], data=retrieved,
        graphJSON=graph_json)


def main():
    """main"""
    app.run()


if __name__ == '__main__':
    main()
