# ECE-061 – Amateur Radio Licence Exam Scheduling and Result Engine — Sample Data Pack
Prepared by 10 SECONDS for Team E036.

This pack is the input for the college ham radio club's ASOC exam engine: 80 applicants, 6 exam sessions between October 2026 and January 2027, four application batches and 67 score sheets (an applicant's rows for one session). Past results before October 2026 are in `past_results.csv`.

Pack conventions where the brief is silent: `correct` may be in half marks; section % = correct / total × 100 rounded to the nearest whole number with halves rounded UP. MORSE rows carry the words per minute copied in `correct` and the required 5 in `total`; PASS when correct ≥ 5. A section pass is carried forward when the new exam date is on or before the pass date + 12 calendar months (same date counts), within the same grade only, and only from a sitting where the section was actually passed (EXEMPT does not renew the window). Consecutive failures count FAIL results in the same grade going back from the latest; an ABSENT neither counts as a failure nor breaks the streak; cooling runs from the latest failed exam date. An applicant's absences = ABSENT results in past_results.csv plus ABSENT outcomes in this cycle. Allotment runs at BATCH_END: normal-priority applications in file order, then LOW-priority ones in file order; each goes to the earliest session of the applied grade dated after the batch date, with a free seat, that also satisfies the cooling period. Age is checked on the exam date of that session.

## Files
| File | What it holds | Rows |
|---|---|---|
| applicants.csv | Registered applicants | 80 |
| past_results.csv | Exam results before this cycle (one row per sitting) | 26 |
| sessions.csv | Exam sessions with seats and grade | 6 |
| scores.csv | Section scores per applicant per session | 145 |
| commands.txt | Loads, application batches, grading and print commands | 113 |

## Column reference
Conventions: dates `YYYY-MM-DD`; timestamps `YYYY-MM-DD HH:MM:SS` (24h, IST, no timezone suffix); money in Rs as plain decimals (no commas, no symbol); percentages as plain numbers (12.5 = 12.5%); booleans `true`/`false`; IDs uppercase with a fixed prefix.

### applicants.csv
| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| applicant_id | string | APP-nnn | APP-001 … APP-080 | Primary key |
| applicant_name | string | - |  |  |
| gender | string | - | M, F |  |
| date_of_birth | date | YYYY-MM-DD |  | Age ≥ 12 on the exam date |
| grade_applied | string | - | RESTRICTED, GENERAL | Default grade; APPLY carries the grade actually applied for |
| prior_licence_years | integer | years | 0–6 | ≥ 1 makes GENERAL eligible |
| city | string | - |  |  |
| mobile | string | 10 digits | starts 6–9 |  |

### past_results.csv
| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| result_id | string | PRS-nnn | unique |  |
| applicant_id | string | APP-nnn | must exist |  |
| exam_date | date | YYYY-MM-DD | before 2026-10-01 |  |
| grade | string | - | RESTRICTED, GENERAL |  |
| theory_result | string | - | PASS, FAIL, EXEMPT, ABSENT |  |
| rules_result | string | - | PASS, FAIL, EXEMPT, ABSENT |  |
| morse_result | string | - | PASS, FAIL, EXEMPT, ABSENT, NA | NA for RESTRICTED |
| overall_result | string | - | PASS, FAIL, ABSENT |  |

### sessions.csv
| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| session_id | string | SES-nn | SES-01 … SES-06 | Primary key |
| exam_date | date | YYYY-MM-DD |  |  |
| centre | string | - |  |  |
| seats | integer | count |  |  |
| grade_offered | string | - | RESTRICTED, GENERAL |  |

### scores.csv
| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| score_id | string | SCR-nnnn | unique |  |
| session_id | string | SES-nn | must exist |  |
| applicant_id | string | APP-nnn | must exist | No rows at all for an allotted applicant = ABSENT |
| section | string | - | THEORY, RULES, MORSE | A carried-forward section has no row |
| correct | decimal | marks (half marks allowed) / wpm for MORSE |  |  |
| total | integer | marks / 5 for MORSE |  | SES-01 RULES is out of 49 (one question withdrawn) |

## Command file format
`commands.txt` holds one command per line as `COMMAND_NAME|arg1|arg2|...`. Commands must be processed in file order, top to bottom. Lines starting with `#` are comments and blank lines are ignored.

| Command | Arguments (in order) | Meaning |
|---|---|---|
| LOAD_APPLICANTS | file |  |
| LOAD_PAST_RESULTS | file |  |
| LOAD_SESSIONS | file |  |
| LOAD_SCORES | file | Score rows are used when the matching GRADE runs |
| BATCH_START | batch_id \| batch_date | Start collecting applications |
| APPLY | applicant_id \| grade \| timestamp | Validate eligibility; queue for allotment |
| BATCH_END | batch_id | Run allotment for the batch (normal priority first, then LOW) |
| PRINT_SEATING | session_id | Write the seating list |
| GRADE | session_id | Grade the session from scores.csv; allotted applicants with no rows are ABSENT |
| PRINT_RESULTS | session_id | Write the result sheet |
| PRINT_REATTEMPT | as_of_date | Re-attempt eligibility for every applicant whose latest result is FAIL |

`decision` is ALLOTTED or REJECTED; `reason` is one of UNDER_AGE, GRADE_NOT_ELIGIBLE, ALREADY_ALLOTTED, COOLING_PERIOD, NO_SEATS, UNKNOWN_APPLICANT, or LOW_PRIORITY on an ALLOTTED row, else `NONE`. Use `NONE` for an empty session_id or pct (e.g. EXEMPT or ABSENT sections); results are PASS, FAIL, EXEMPT, ABSENT or NA.

## Planted scenarios
Line numbers count the header row as line 1, so the first data row of a CSV is line 2. For commands.txt the line number is the physical line in the file (comment lines included).

- **Applicant turning 12 on the exam date** — APP-071 (Sowmya Desai) born 2014-10-14 applies in batch B1 (commands.txt line 19) and is allotted SES-01 on 2026-10-14 — exactly 12 on the exam date, so eligible. Contrast APP-008 (Vidya Kulkarni) born 2014-10-15 (commands.txt line 18): 11 on 2026-10-14 → REJECTED UNDER_AGE.
- **Section score at exactly 50% after rounding (e.g. 24.5 of 49)** — APP-037 (Lakshmi Hegde) at SES-01: RULES scores.csv line 25 (SCR-0024) = 24.5 of 49 → 50.0% → 50 → PASS (RESTRICTED needs 50). Contrast APP-049 (Jyothi Sharma): RULES scores.csv line 4 (SCR-0003) = 24 of 49 → 48.98% → 49 → FAIL.
- **Section pass exactly 12 months old** — APP-015 (Ramya Kulkarni) passed THEORY on 2025-11-13 (past_results.csv) and sits SES-03 on 2026-11-13 — exactly 12 months later, so THEORY is carried forward (EXEMPT); only RULES is sat (scores.csv line 78 (SCR-0077)). Contrast APP-043 (Shilpa Rao): THEORY pass dated 2025-11-12 is 12 months + 1 day old → no exemption, sits both sections (scores.csv line 68 (SCR-0067)).
- **Re-application on day 30 after failing** — APP-050 (Karthik Patil) fails SES-03 on 2026-11-13 (THEORY scores.csv line 66 (SCR-0065) = 22/50 → 44%) and re-applies in batch B3 (commands.txt line 82); the earliest RESTRICTED session SES-05 on 2026-12-13 is exactly day 30 → allowed. The same day-30 case applies to SES-01 failures re-applying in B2 for SES-03 (2026-10-14 → 2026-11-13).
- **Session full when the last applicant in a batch applies** — Batch B1: SES-02 (GENERAL, 10 seats) is filled by the first 10 eligible GENERAL applications; the LAST line of the batch, APP-036 (Sachin Patel) at commands.txt line 46, finds SES-02 full and is allotted the next GENERAL session SES-04.

Extra traps (realistic things your validation should catch):

- **Third consecutive failure → 90-day gap** — APP-056 (Prakash Verma) has two RESTRICTED FAILs in past_results.csv (2026-03-11, 2026-06-10) and fails SES-01 (scores.csv line 19 (SCR-0018) = 21/50). Re-applying in B2 (commands.txt line 61) needs a session on or after 2027-01-12; no RESTRICTED session exists → REJECTED COOLING_PERIOD.
- **Cooling period skips a session** — APP-064 (Ajay Sharma) fails SES-02 (GENERAL, 2026-10-28; RULES scores.csv line 35 (SCR-0034) = 26/50 → 52%) and re-applies in B2 (commands.txt line 67); SES-04 on 2026-11-25 is only day 28, so allotment goes to SES-06 (2027-01-15).
- **Two absences → LOW priority** — APP-007 (Sahana Bhat) was ABSENT on 2026-06-10 (past_results.csv) and is ABSENT again at SES-01 (no score rows). In B2 it is the FIRST application (commands.txt line 56) but is allotted after every other applicant: SES-03 fills with the normal applicants and it lands in SES-05. APP-019 (Manoj Singh) is ABSENT at SES-01 too but has only one absence, so stays normal priority.
- **One future allotment at a time** — APP-038 (Rahul Rao) was allotted SES-03 in B1 and applies again in B2 (commands.txt line 59) → REJECTED ALREADY_ALLOTTED.
- **GENERAL eligibility** — APP-052 (Sachin Shetty) applies GENERAL in B1 (commands.txt line 30) with 0 prior licence years and no RESTRICTED pass → REJECTED GRADE_NOT_ELIGIBLE; APP-040 (Anjali Menon) has exactly 1 prior year → eligible.
- **GENERAL pass-mark boundary and Morse** — APP-001 (Suresh Shetty) at SES-04: THEORY scores.csv line 97 (SCR-0096) = 59.5 of 100 → 59.5% → 60 → PASS, Morse 5 wpm = PASS. APP-010 (Pallavi Desai) at SES-02 passes THEORY and RULES but MORSE scores.csv line 33 (SCR-0032) = 4 wpm → FAIL overall.
- **Unknown applicant** — commands.txt line 83 APPLY|APP-099 → error line, no seat consumed.

## What is NOT in this pack
Expected outputs are not provided for this set. Validate your engine with your own test suite against the rules in your brief (BR-01 … BR-07). A separate hidden input set with the same schema will be used at final evaluation; outputs are compared field-for-field, so follow the column formats above exactly in your own output.

## Output format expected at evaluation
Produce these files (CSV, header row, same conventions as above). Column order matters.

### apply_log.csv
One row per APPLY in commands.txt order.

Columns in order: `line_no`, `batch_id`, `applicant_id`, `grade`, `decision`, `session_id`, `reason`

### seating.csv
One row per seat, per PRINT_SEATING, seat_no in allotment order.

Columns in order: `session_id`, `exam_date`, `seat_no`, `applicant_id`, `applicant_name`, `grade`, `priority`

### results.csv
One row per allotted applicant per GRADE, sorted by applicant_id within session.

Columns in order: `session_id`, `applicant_id`, `grade`, `theory_pct`, `theory_result`, `rules_pct`, `rules_result`, `morse_wpm`, `morse_result`, `overall_result`

### reattempt.csv
One row per applicant with a latest FAIL, sorted by applicant_id.

Columns in order: `applicant_id`, `grade`, `last_exam_date`, `consecutive_failures`, `cooling_days`, `earliest_eligible_exam_date`


---

## Implementation and verification

### Environment
- Python 3.10 or newer
- VS Code (or any Python editor)
- pytest for automated tests

### Setup on Windows (PowerShell)
Run these commands from the project root:

```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If Python 3.10 is not installed, use an installed Python 3 version that is 3.10 or newer.

### Run the engine

```powershell
python .\src\main.py
```

Optional command/data/output paths:

```powershell
python .\src\main.py --commands commands.txt --data-dir .\data --output-dir .\outputs
```

The command file and every `LOAD_*` filename are resolved inside the selected data directory. Input paths cannot escape that directory.

### Run automated tests

```powershell
python -m pytest -q
```

The test suite checks rounding, month-boundary calculations, age on exam date, grade eligibility, duplicate applications, seat priority, cooling periods, section exemptions, independent section grading, Morse requirements, unknown applicants, reattempt reporting and output schemas.

### Output files
The engine writes the four required CSV files into `outputs/`:
- `apply_log.csv`
- `seating.csv`
- `results.csv`
- `reattempt.csv`

Column names and order are defined centrally in `src/main.py` and match the evaluation schema in this README.

### Design and project decisions
See:
- `docs/DESIGN_DOCUMENT.md`
- `docs/DECISION_LOG.md`

### Reproducibility
The supplied `data/` files are the sample input pack. The automated integration test copies these files to a temporary directory and writes outputs there, so the original input files are not modified.
