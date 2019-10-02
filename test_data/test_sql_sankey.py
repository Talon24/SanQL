"""Test the sql_sankey function."""

import json
import pytest

import sql_sankey


class NoException(Exception):
    """Raise to check if no other exception was raised before."""


def test_find_json():
    """Check if json is found correctly in the input."""
    assert sql_sankey.find_json("test data") == "test data"
    verticastring = (
        "------------------------------ \n"
        "QUERY PLAN DESCRIPTION: \n"
        "------------------------------ \n"
        "JSON format:\n"
        "test data\n"
        "End JSON format")
    assert sql_sankey.find_json(verticastring) == "test data\n"


def test_generate():
    """test the generation"""
    with open("test_data/postgres.json") as file:
        data = json.load(file)
    with pytest.raises(NoException):
        sql_sankey.generate(data, to_json=True)
        raise NoException


def test_prettifier():
    """Test if the prettifier works correct."""
    result = sql_sankey.prettify_details(
        {"a": 2, "bcd": 345, "e": "fgh", "i": True, "__not": "invis",
         "float": 123.456})
    assert result == (
        "╔═══════╦═════════════════╗<br />"
        "║ a     ║            2.00 ║<br />"
        "║ bcd   ║          345.00 ║<br />"
        "║ e     ║             fgh ║<br />"
        "║ i     ║            True ║<br />"
        "║ float ║          123.46 ║<br />"
        "╚═══════╩═════════════════╝")


if __name__ == "__main__":
    pytest.main()
