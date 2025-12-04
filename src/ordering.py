"""Contains functions for ordering prioritized pairs."""

import networkx as nx
import pandas as pd


def make_baseline_predict(primary_col, secondary_col):
    """Baseline ordering heuristic.

    Args:
        row: A single row of the log.
        primary_col: The name of the primary heuristic column (as a dict).
        secondary_col: The name of the secondary heuristic column (as a dict).

    Returns:
        A function that takes a single row of the log and returns a prediction.
    """
    primary_col, primary_val_type = primary_col["heuristic"], primary_col["value_type"]
    secondary_col, secondary_val_type = secondary_col["heuristic"], secondary_col["value_type"]

    def predict(row):
        value_left = row[f"{primary_col} (Left {primary_val_type})"]
        value_right = row[f"{primary_col} (Right {primary_val_type})"]

        if value_left > value_right:
            return 1
        elif value_right > value_left:
            return 0

        # TIE → use secondary heuristic
        value_left = row[f"{secondary_col} (Left {secondary_val_type})"]
        value_right = row[f"{secondary_col} (Right {secondary_val_type})"]

        if value_left > value_right:
            return 1
        return 0

    return predict


def make_baseline_tiebreak(secondary_col):
    """Tiebreak function to be used with the baseline oredering heuristic.

    Arguments:
        secondary_col -- The name of the secondary heuristic column (as a dict).
    Returns:
        A function that takes a single row of the log and returns a tiebreak score.
    """
    secondary_col, secondary_val_type = secondary_col["heuristic"], secondary_col["value_type"]

    def predict(row):
        value_left = row[f"{secondary_col} (Left {secondary_val_type})"]
        value_right = row[f"{secondary_col} (Right {secondary_val_type})"]
        return value_left - value_right

    return predict


def rank_submission(submission_df: pd.DataFrame, prediction_col: str, tiebreak_col: str):
    """
    Rank all defects in a single submission from pairwise predictions.

    Args:
        submission_df: All rows corresponding to a single submission.
        prediction_col: Name of column containing pairwise predictions.
        tiebreak_col: Name of column containing pairwise tiebreak scores.
    Returns:
        List of nodes in ranked order (highest rank first).
    """
    # Build full directed graph of pairwise decisions
    G = nx.DiGraph()

    nodes = pd.unique(submission_df[["left", "right"]].values.ravel())
    G.add_nodes_from(nodes)

    for _, row in submission_df.iterrows():
        left = row["left"]
        right = row["right"]
        pred = row[prediction_col]
        tiebreak = row[tiebreak_col]

        if pred == 1:
            G.add_edge(left, right, tiebreak=tiebreak)
        else:
            G.add_edge(right, left, tiebreak=-tiebreak)

    # Topological sort with cycle-breaking
    ranked_nodes = []
    while len(G) > 0:
        # Nodes with zero in-degree (sources)
        zero_in = [n for n, d in G.in_degree() if d == 0]

        if zero_in:
            # Break ties by sum of outgoing tiebreak scores
            scores = {n: sum(data["tiebreak"] for _, _, data in G.out_edges(n, data=True)) for n in zero_in}
            next_node = max(scores, key=scores.get)
        else:
            # Cycle exists → pick node with lowest "net in vs out tiebreak"
            scores = {}
            for n in G.nodes():
                out_score = sum(data["tiebreak"] for _, _, data in G.out_edges(n, data=True))
                in_score = sum(data["tiebreak"] for _, _, data in G.in_edges(n, data=True))
                scores[n] = out_score - in_score  # higher is more "dominant"
            # Remove node with highest dominance first
            next_node = max(scores, key=scores.get)

        ranked_nodes.append(next_node)
        G.remove_node(next_node)

    return ranked_nodes
