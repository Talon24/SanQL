"""Test the functionality of the walkers."""

import json

import pytest

# import walkers.postgres
# import walkers.vertica
import sql_sankey


def test_walking_finishing():
    """See if amount of walker's steps is right."""
    with open("test_data/postgres.json") as file:
        data = json.load(file)
    walker = sql_sankey.walker(data)
    counter = 0
    for _ in walker:
        counter += 1
    assert counter == 7


def test_walking_result():
    """Result must be same"""
    with open("test_data/postgres.json") as file:
        data = json.load(file)
    walker = sql_sankey.walker(data)
    with open("test_data/postgres_result.txt") as file:
        for thing in walker:
            assert str(thing) == file.readline().rstrip()


if __name__ == '__main__':
    pytest.main()
