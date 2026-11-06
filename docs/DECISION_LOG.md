# Decision Log
## E036-ECE-061 — Amateur Radio Licence Exam Scheduling and Result Engine

| ID | Decision | Rationale |
|---|---|---|
| D-01 | Use Python 3.10+ and CSV files | Matches the project technology and supplied sample pack; keeps setup simple. |
| D-02 | Use a pipe-delimited command file | Preserves the required explicit processing sequence and batch boundaries. |
| D-03 | Use dictionaries keyed by applicant/session IDs | Provides clear, direct lookup without a database. |
| D-04 | Allocate normal-priority applications before LOW-priority applications | Implements the specified two-tier priority rule while preserving file order within each tier. |
| D-05 | Evaluate age against each candidate session date | An applicant may be too young for an earlier session but eligible for a later one. |
| D-06 | Treat GENERAL eligibility as a previous RESTRICTED overall pass or at least one prior licence year | Implements the stated alternative eligibility conditions. |
| D-07 | Use `Decimal` with `ROUND_HALF_UP` for percentages | Avoids floating-point boundary errors and implements half-up rounding. |
| D-08 | Carry a section pass through the same-grade 12-calendar-month window, inclusive | Matches the sample-pack convention; an EXEMPT result does not renew the window. |
| D-09 | Start cooling from the latest failed sitting; skip absences in the failure streak | Matches the sample-pack convention and supports the 30-/90-day rules. |
| D-10 | Treat a sitting with zero score rows as ABSENT | Distinguishes a complete absence from a partial score sheet. |
| D-11 | Assign LOW priority after two or more absences | Implements the stated attendance rule; normal applicants are processed first. |
| D-12 | Reject an applicant who already has a future allotment | Prevents simultaneous future examination seats for one applicant. |
| D-13 | Resolve input filenames inside the data directory | Supports the command format while preventing path traversal outside the input folder. |
| D-14 | Filter reattempt history by the report's as-of date | Prevents future-dated results from affecting a historical report. |
| D-15 | Preserve the sample command sequence when SES-03 is full | APP-015 is not forced into SES-03 merely to trigger an example; the exact 12-month exemption is tested separately. |

## Known interpretation notes

- The sample pack explicitly defines 12 months as a calendar-month boundary, inclusive of the matching date.
- For a partial score sheet, each required section is decided independently. If a section has neither a score nor a valid exemption, it fails.
- Application order means physical command-file order; timestamps are validated but do not reorder commands.
