# 5-Minute Demo Script — E036-ECE-061

## 0:00–0:30 — Introduction
- State the project title, project ID and team members.
- Explain that this is a Python command-file-driven exam scheduling and result engine.
- Mention the four input CSV types and four output reports.

## 0:30–1:15 — Project structure
- Show `src/main.py`, `data/`, `tests/`, `docs/` and `outputs/`.
- Briefly identify applicants, past results, sessions, scores and commands.
- Show the command file's LOAD, BATCH_START, APPLY and BATCH_END sequence.

## 1:15–2:15 — Run the application
- Open the project terminal.
- Run `python .\\src\\main.py`.
- Show the four output files and their row counts.
- Open `apply_log.csv` and show decisions and rejection reasons.

## 2:15–3:15 — Demonstrate business rules
- Show APP-071's age eligibility on the exact 12th birthday.
- Show APP-052 rejected for GENERAL eligibility and APP-040 accepted.
- Show APP-007 receiving LOW priority after two absences.
- Show APP-050's day-30 reattempt and APP-056's 90-day cooling period.
- Show APP-037's 24.5/49 rounding to 50% and APP-010 failing Morse at 4 WPM.
- Explain that APP-015 is not forced into a full session; the exact exemption boundary has a separate unit test.

## 3:15–4:15 — Automated tests
- Run `python -m pytest -q`.
- Show the test summary.
- Mention that tests include both focused rule tests and a full sample-data integration test.

## 4:15–5:00 — Outputs and close
- Briefly show `seating.csv`, `results.csv` and `reattempt.csv`.
- Show the design document and decision log.
- State that the repository is named `E036-ECE-061` and identify the submission contact.
- End with a concise summary of the implemented workflow.
