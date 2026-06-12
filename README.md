# Job Search Sankey Tracker

This project tracks job applications in Excel and automatically turns the tracker into an interactive Sankey diagram. It is meant to show how your applications flow into outcomes like interviews, rejections, ghosting, and offers.

## What is included

- `applications_template.xlsx` — Excel tracker with dropdowns, sample rows, and a small dashboard.
- `generate_sankey.py` — Python script that reads the Excel file and creates an interactive HTML Sankey diagram.
- `requirements.txt` — Python dependencies.

## Why this project exists

Job searching can feel random and discouraging. A Sankey diagram makes the process visible. Instead of only thinking, “I got rejected,” you can see the full pipeline:

`Applications → Interviews → Offers → Accepted / Declined`

This is useful as a personal tracker, a GitHub portfolio project, and a small data visualization project.

## How the Excel file works

Open `applications_template.xlsx` and go to the `Applications` sheet. Each row represents one job application.

Important columns:

- `Company`
- `Position`
- `Date Applied`
- `Source`
- `Resume Version`
- `Current Stage`
- `Outcome`
- `Follow-Up Date`
- `Notes`

Use the dropdowns for `Current Stage`, `Outcome`, `Source`, and `Resume Version`. You can edit the dropdown options on the `Lists` sheet.

The `Summary` sheet gives quick counts, but the Python script is what generates the Sankey diagram.

## Setup

Install Python 3.10 or newer, then install the project dependencies:

```bash
pip install -r requirements.txt
```

## Generate the Sankey diagram

From the project folder, run:

```bash
python generate_sankey.py
```

This creates:

```text
job_search_sankey.html
```

Open that file in your browser to view the interactive chart.

## Optional custom command

You can choose a different Excel input or output file name:

```bash
python generate_sankey.py --input applications_template.xlsx --output my_sankey.html
```

## Recommended GitHub repo structure

```text
job-search-sankey-tracker/
├── applications_template.xlsx
├── generate_sankey.py
├── requirements.txt
├── README.md
└── .gitignore
```

## Suggested future improvements

- Add charts for applications per week.
- Add a resume-version success rate report.
- Add a source success rate report, such as LinkedIn vs USAJobs vs referrals.
- Export the chart as a PNG.
- Add a Streamlit dashboard.

## Notes

The script treats terminal outcomes like `Rejected`, `Ghosted`, `Offer Accepted`, `Offer Declined`, and `Withdrawn` as final destinations. Active applications flow to their current stage.
