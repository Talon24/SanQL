[![Build Status](https://travis-ci.com/Talon24/SanQL.svg?branch=master)](https://travis-ci.com/Talon24/SanQL)
![License: MIT](https://img.shields.io/badge/License-MIT-purple.svg)
[![Updates](https://pyup.io/repos/github/Talon24/SanQL/shield.svg)](https://pyup.io/repos/github/Talon24/SanQL/)
[![Python 3](https://pyup.io/repos/github/Talon24/SanQL/python-3-shield.svg)](https://pyup.io/repos/github/Talon24/SanQL/)


# SanQL
Visualize SQL explain plans with a sankey diagram.

Convert an explain plan from a database into a graph that lets you easily see which steps produce costs and where optimization might be useful.
![Explain-Plan shown as a sankey-diagram](images/sankey.png)

Detailed information about the processes can be retrieved by hovering over the connections
![Explain-Plan as diagram with additional info shown](images/hover.png)

The thickness of the outgoing connections represent the calculated cost for the desired action.
If your plan was generated by explain-analyze, the thickness will instead represent the real elapsed time.

The Graph will be shown in the browser. The basic variant will launch a desktop application where the plan can be entered which then launches a new browser tab. A server version, that will work all-inside the browser is Work in Progress.

## Supported Databases
- Postgres
- Vertica

If you want additional databases to be supported, open a feature request and include a json-formatted explainplan. The more explain-plans, the easier the process will be. Mark them whether they are normal explain-plans or explain-analyze-plans.
