"""Application to simulate tracking how students progress and what would the priotization strategies recommend."""

import math
from pathlib import Path

import dash
import dash_bootstrap_components as dbc
import numpy as np
import pandas as pd
import plotly.graph_objs as go
import plotly.subplots as sp
from dash import Input, Output, dcc, html

####################################################################################################
##                                            Layout                                              ##
####################################################################################################

USER_ID = 2121562

data_path = Path("data/ipython_old/cache/")

log = pd.read_csv(data_path / "log.csv", sep=";", header=0, index_col=0)
log["time"] = pd.to_datetime(log["time"])
items = pd.read_csv(data_path / "items.csv", sep=";", header=0, index_col=0)
defects = pd.read_csv(data_path / "defects.csv", sep=";", header=0, index_col=0)
defect_log = pd.read_csv(data_path / "defect_log.csv", sep=";", header=0, index_col=0)

user_history = log[log["user"] == USER_ID].sort_values("time")
if user_history.shape[0] == 0:
    raise ValueError("No history for this user.")
is_final = np.append(user_history["item"].iloc[:-1].values != user_history["item"].iloc[1:].values, True)
user_history["session_id"] = is_final.cumsum() - is_final

####################################################################################################
##                                            Layout                                              ##
####################################################################################################

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

rows = math.floor(math.sqrt(user_history["session_id"].max()))
cols = math.ceil(user_history["session_id"].max() / rows)

session_figure = sp.make_subplots(rows=rows, cols=cols)
for session_id in np.unique(user_history["session_id"]):
    session_data = user_history[user_history["session_id"] == session_id]
    session_figure.add_trace(
        go.Scatter(x=session_data["time"], y=session_data["item"], mode="markers"),
        row=math.ceil(session_id / cols) + 1,  # row index starts at 1
        col=session_id % cols + 1,  # col index starts at 1
    )

session_graph = dcc.Graph(
    id="session-graph",
    figure=session_figure,
)

student_profile = dcc.Graph(
    id="student-profile",
    figure={"data": [go.Bar(x=["A", "B", "C"], y=[10, 11, 12])], "layout": go.Layout(title="Student Profile")},
)

task_description = html.Div(id="task-description")

task_profile = dcc.Graph(
    id="task-profile",
    figure={"data": [go.Bar(x=["X", "Y", "Z"], y=[5, 7, 8])], "layout": go.Layout(title="Task Profile")},
)

defect_grid = [html.Button(f"Defect {i}", id=f"defect-button-{i}") for i in range(1, 7)]
strategy_grid = [html.Button(f"Strategy {i}", id=f"strategy-button-{i}") for i in range(1, 7)]

app.layout = dbc.Container(
    children=[
        dbc.Row(
            children=[
                dbc.Col(
                    children=[session_graph, student_profile],
                    width=4,
                ),
                dbc.Col(
                    children=[task_description, task_profile],
                    width=4,
                ),
                dbc.Col(
                    children=[
                        html.Div(
                            children=defect_grid,
                            style={"display": "flex", "flexDirection": "column", "gap": "10px"},
                        ),
                        html.Div(
                            children=strategy_grid, style={"display": "flex", "flexDirection": "column", "gap": "10px"}
                        ),
                    ],
                    width=4,
                ),
            ]
        )
    ],
    fluid=True,
)

####################################################################################################
##                                           Callbacks                                            ##
####################################################################################################


@app.callback(
    Output("task_description", "children"),  # Output the task description
    [Input("session-graph", "clickData")],  # Triggered by clicking on session graph
)
def update_task_description(clickData):
    if clickData is None:
        return html.Div([html.H5("Task Description"), html.P("Click on a point on the graph to see more details.")])

    # Extract the clicked point's information
    point_data = clickData["points"][0]
    x_value = point_data["x"]
    y_value = point_data["y"]

    # Update the task description based on the clicked point
    return html.Div(
        [
            html.H5(f"Task Description at x = {x_value}, y = {y_value}"),
            html.P(
                f"The point you clicked on has x = {x_value} and y = {y_value}. Here is the task description for this point."
            ),
        ]
    )


if __name__ == "__main__":
    app.run_server(debug=True)
