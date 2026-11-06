# Design Document
## E036-ECE-061 — Amateur Radio Licence Exam Scheduling and Result Engine

**Team:** E036  
**Members:** Shivaraj Patil and Sindhu  
**Technology:** Python 3.10+  
**Interface:** Pipe-delimited command file; CSV input and output

## 1. Purpose

The application processes amateur-radio examination applications, allocates eligible applicants to future examination sessions, grades section scores, applies exemptions and cooling periods, and produces auditable CSV reports.

## 2. System context

The engine is a local, batch-oriented Python application. It reads applicant, past-result, session and score CSV files. A command file controls load order, application batches, seating reports, grading and reattempt reporting. It does not require a database or network connection.

## 3. Main components

| Component | Responsibility |
|---|---|
| CSV input layer | Reads and validates source records |
| Command processor | Executes commands in file order and reports line-specific errors |
| Eligibility validator | Checks age, requested grade and existing future allotments |
| Batch allotment engine | Queues applications and assigns seats in priority order |
| Result engine | Calculates section results, exemptions and overall outcome |
| Reattempt engine | Calculates failure streaks and cooling dates |
| CSV output layer | Writes the four required reports in fixed column order |

## 4. Processing flow

1. Load applicants.
2. Load past results, sessions and score sheets.
3. Read commands from top to bottom.
4. At `BATCH_START`, record the batch date and begin collecting applications.
5. At `APPLY`, reject unknown applicants, invalid grades, applicants with a future allotment, and applicants who do not meet GENERAL eligibility. Queue remaining applications.
6. At `BATCH_END`, process normal-priority applications in command-file order, followed by LOW-priority applications in command-file order.
7. For each queued application, find the earliest future session of the requested grade that satisfies age and cooling rules and has a free seat.
8. At `PRINT_SEATING`, write the allocated seats in allotment order.
9. At `GRADE`, evaluate each allotted applicant. No score rows for the sitting means ABSENT.
10. At `PRINT_REATTEMPT`, report applicants whose latest result as of the requested date is FAIL.
11. Write the four consolidated CSV output files.

## 5. Business rules

### Eligibility
- Applicant must be at least 12 years old on the selected examination date.
- GENERAL requires either a previous RESTRICTED overall pass or at least one year of prior licence experience.
- Eligibility is evaluated against the application/batch date for previous results and against each candidate session date for age.

### Allotment
- Only sessions later than the batch date are considered.
- Requested grade must match the session's offered grade.
- Earliest eligible session with a free seat is selected.
- Application order is retained within each priority group.
- Applicants with at least two recorded absences are LOW priority.
- A person cannot hold more than one future allotment.

### Assessment
- RESTRICTED THEORY and RULES pass at 50% each.
- GENERAL THEORY and RULES pass at 60% each.
- GENERAL MORSE passes at 5 WPM.
- Each section is assessed independently.
- Percentages use decimal arithmetic and ROUND_HALF_UP, so a half rounds upward.
- Overall PASS requires every required section to be PASS or EXEMPT.

### Exemptions
A section passed in the same grade is exempt when the new examination date is on or before the date 12 calendar months after the pass date. Only an actual PASS creates an exemption; an EXEMPT result does not renew the period.

### Cooling and absences
- A failure normally requires 30 calendar days before the next eligible examination date.
- Three or more consecutive failures in the same grade require 90 days.
- ABSENT sittings do not count as failures and do not break a failure streak.
- A sitting with no score rows is ABSENT.
- Two or more absences cause LOW priority.

## 6. Data structures and algorithms

The engine uses dictionaries keyed by applicant ID and session ID for direct record lookup. Past and current results are grouped by applicant. Scores are grouped by `(session_id, applicant_id)` and section. Allotments are grouped by session.

Batch allocation uses a stable two-pass ordering: normal priority first, then LOW priority. Each application scans matching sessions sorted by examination date and takes the first session satisfying all constraints with a free seat.

Percentages use `Decimal` rather than binary floating-point arithmetic to avoid rounding-boundary errors.

## 7. Error handling and validation

The program validates duplicate identifiers, dates, numeric seat counts, grades, score references, score sections, duplicate section scores and command arguments. Command errors include the physical line number and original command text. Input filenames are restricted to the configured data directory.

## 8. Outputs

| Output | Purpose |
|---|---|
| `apply_log.csv` | One decision row per APPLY command |
| `seating.csv` | One row per allocated seat and seating print command |
| `results.csv` | One result row per allotted applicant per graded session |
| `reattempt.csv` | Latest failed grade, failure streak, cooling days and earliest eligible date |

The output column names and order match the project README evaluation specification.

## 9. Testing strategy

The pytest suite combines focused unit tests and a full sample-data integration test. It checks rounding boundaries, month arithmetic, age, grade eligibility, seat priority, duplicate applications, cooling periods, exemption cut-offs, score thresholds, Morse WPM, unknown applicants, reattempt as-of filtering, row counts and exact output headers.

Run with:

```powershell
python -m pytest -q
```

## 10. Limitations and assumptions

- The application is a local command-file processor, not a web application.
- The sample data pack defines the calendar-month interpretation of the 12-month exemption.
- The command file is authoritative for application processing order.
- A partial score sheet is graded section by section; a required section without a score or exemption is FAIL. A sitting with no score rows at all is ABSENT.
