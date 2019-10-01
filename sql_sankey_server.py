"""Start a server"""

import json

# from flask import Flask, session, redirect, url_for, request, jsonify, render_template
from flask import Flask
from flask import render_template
from flask import request

import sql_sankey

app = Flask(__name__)  # pylint: disable=invalid-name


@app.route("/", methods=["GET"])
def onlyform():
    """Welcome page"""
    return """
        <form method="post">
            <p>Query <textarea rows="40" cols="80" name=Query></textarea>
            <p><input type=submit value=Visualize>
        </form>
    """


@app.route("/", methods=["POST"])
def index():
    """Base."""
    data = request.form["Query"]
    data = json.loads(data)
    graph_json = sql_sankey.generate(data, to_json=True)
    return render_template(
        'index.html',
        ids=["Graph"],
        graphJSON=graph_json)


def main():
    """main"""
    app.run()


if __name__ == '__main__':
    main()
