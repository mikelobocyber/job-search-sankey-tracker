"""Generate an interactive Sankey diagram from the Excel job application tracker.

Usage:
    python generate_sankey.py
    python generate_sankey.py --input applications_template.xlsx --output sankey.html
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go

# These are the outcomes that mean an application is finished.
# If a row has one of these outcomes, the script sends it straight to that final bucket.
TERMINAL_OUTCOMES = {"Rejected", "Ghosted", "Offer Accepted", "Offer Declined", "Withdrawn"}

# I use this label when an application is still alive and moving through the process.
ACTIVE_OUTCOME = "Active"


def clean_text(value: object) -> str:
    """Turn spreadsheet values into clean text that is safe to compare."""
    # Excel cells can be blank, and pandas reads many blanks as NaN.
    # Returning an empty string makes the rest of the code easier to read.
    if pd.isna(value):
        return ""

    # Strip removes accidental spaces, like "Rejected " instead of "Rejected".
    return str(value).strip()


def add_link(link_counts: dict[tuple[str, str], int], source: str, target: str, value: int = 1) -> None:
    """Add one flow line to the Sankey data, or increase it if it already exists."""
    # A Sankey link needs a valid starting point, ending point, and positive value.
    # This guard keeps bad or empty spreadsheet rows from creating weird chart entries.
    if not source or not target or value <= 0:
        return

    # The dictionary key is a pair like ("Applications", "Rejected").
    # If several rows have the same path, we count them together so the chart stays clean.
    link_counts[(source, target)] = link_counts.get((source, target), 0) + value


def build_links(df: pd.DataFrame) -> dict[tuple[str, str], int]:
    """Build Sankey flows from one-row-per-application tracker data."""
    link_counts: dict[tuple[str, str], int] = {}

    # Each spreadsheet row is one job application.
    # The script only needs Company, Current Stage, and Outcome to build the diagram.
    for _, row in df.iterrows():
        company = clean_text(row.get("Company"))

        # If there is no company name, this is probably a blank/example row, so skip it.
        if not company:
            continue

        # If the stage is blank, assume the application was at least submitted.
        stage = clean_text(row.get("Current Stage")) or "Applied"

        # If the outcome is blank, treat it as active instead of finished.
        outcome = clean_text(row.get("Outcome")) or ACTIVE_OUTCOME

        # Finished applications go from Applications directly to their final outcome.
        if outcome in TERMINAL_OUTCOMES:
            add_link(link_counts, "Applications", outcome)

        # Active applications flow to the stage they are currently in.
        elif outcome == ACTIVE_OUTCOME:
            add_link(link_counts, "Applications", stage)

        # This keeps the script flexible if you add custom outcomes later.
        else:
            add_link(link_counts, "Applications", outcome)

    return link_counts


def sorted_nodes(link_counts: dict[tuple[str, str], int]) -> list[str]:
    """Return chart nodes in a predictable order so the diagram is easier to read."""
    # Plotly can choose an order by itself, but a hand-picked order makes the chart
    # feel more like a job pipeline: applied, assessments, interviews, offers, outcomes.
    preferred_order = [
        "Applications",
        "Applied",
        "Online Assessment",
        "Phone Screen",
        "First Round Interview",
        "Second Round Interview",
        "Third Round Interview",
        "Final Round Interview",
        "Offer Received",
        "Offer Accepted",
        "Offer Declined",
        "Rejected",
        "Ghosted",
        "Withdrawn",
    ]

    # Collect every unique source and target from the links.
    nodes = set()
    for source, target in link_counts:
        nodes.add(source)
        nodes.add(target)

    # Keep the common pipeline stages first, then add any custom stages alphabetically.
    ordered = [node for node in preferred_order if node in nodes]
    ordered.extend(sorted(nodes - set(ordered)))
    return ordered


def make_sankey(link_counts: dict[tuple[str, str], int], output_path: Path) -> None:
    """Create the Plotly Sankey chart and save it as an HTML file."""
    if not link_counts:
        raise ValueError("No usable applications found. Add rows with at least a Company name.")

    # Plotly wants nodes as numbers, not names, so we create an index for each label.
    nodes = sorted_nodes(link_counts)
    node_index = {node: idx for idx, node in enumerate(nodes)}

    sources: list[int] = []
    targets: list[int] = []
    values: list[int] = []

    # Convert links like ("Applications", "Rejected") into numeric Plotly arrays.
    # Sorting by count puts the biggest flows first in the data, which makes debugging nicer.
    for (source, target), value in sorted(link_counts.items(), key=lambda item: (-item[1], item[0])):
        sources.append(node_index[source])
        targets.append(node_index[target])
        values.append(value)

    # Build totals so the labels say things like "Rejected: 12" instead of just "Rejected".
    totals_by_node = {node: 0 for node in nodes}
    for (_, target), value in link_counts.items():
        totals_by_node[target] = totals_by_node.get(target, 0) + value

    # The Applications node should show the total number of tracked applications.
    total_apps = sum(value for (source, _), value in link_counts.items() if source == "Applications")
    totals_by_node["Applications"] = total_apps

    labels = [f"{node}: {totals_by_node.get(node, 0)}" for node in nodes]

    # This is the actual Sankey diagram. The node section controls the boxes.
    # The link section controls the flow lines between those boxes.
    fig = go.Figure(
        data=[
            go.Sankey(
                arrangement="snap",
                node={
                    "pad": 18,
                    "thickness": 18,
                    "line": {"color": "black", "width": 0.5},
                    "label": labels,
                },
                link={"source": sources, "target": targets, "value": values},
            )
        ]
    )

    # The output is an HTML file, so you can open it in a browser or share it easily.
    fig.update_layout(
        title_text="Job Search Sankey Diagram",
        font_size=12,
        width=1100,
        height=700,
    )
    fig.write_html(output_path, include_plotlyjs="cdn")


def print_summary(df: pd.DataFrame) -> None:
    """Print a small terminal summary after the chart is generated."""
    # This gives quick feedback without needing to open the HTML file immediately.
    total = int(df["Company"].notna().sum()) if "Company" in df else 0
    print(f"Applications tracked: {total}")

    if "Outcome" in df:
        print("
Outcome counts:")
        print(df["Outcome"].dropna().astype(str).str.strip().value_counts().to_string())

    if "Current Stage" in df:
        print("
Current stage counts:")
        print(df["Current Stage"].dropna().astype(str).str.strip().value_counts().to_string())


def main() -> None:
    """Read the Excel file, build the Sankey data, and generate the chart."""
    # argparse lets you run the script with custom file names from the terminal.
    parser = argparse.ArgumentParser(description="Generate a Sankey chart from an Excel job tracker.")
    parser.add_argument("--input", default="applications_template.xlsx", help="Path to the Excel tracker.")
    parser.add_argument("--output", default="job_search_sankey.html", help="Output HTML file.")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    # This error message is meant to be clear for someone running the repo the first time.
    if not input_path.exists():
        raise FileNotFoundError(f"Could not find {input_path}. Run the script from the project folder.")

    # Read the Applications sheet from the Excel workbook.
    # Empty rows are removed so they do not count as real applications.
    df = pd.read_excel(input_path, sheet_name="Applications")
    df = df.dropna(how="all")

    # Turn the spreadsheet rows into Sankey links, draw the chart, then print a summary.
    link_counts = build_links(df)
    make_sankey(link_counts, output_path)
    print_summary(df)
    print(f"
Created: {output_path.resolve()}")


if __name__ == "__main__":
    main()
