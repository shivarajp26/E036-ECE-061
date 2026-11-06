from __future__ import annotations

import argparse
import csv
import sys
import calendar
from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUTPUTS = ROOT / "outputs"

OUTPUT_COLUMNS = {
    "apply_log.csv": ["line_no", "batch_id", "applicant_id", "grade", "decision", "session_id", "reason"],
    "seating.csv": ["session_id", "exam_date", "seat_no", "applicant_id", "applicant_name", "grade", "priority"],
    "results.csv": ["session_id", "applicant_id", "grade", "theory_pct", "theory_result", "rules_pct", "rules_result", "morse_wpm", "morse_result", "overall_result"],
    "reattempt.csv": ["applicant_id", "grade", "last_exam_date", "consecutive_failures", "cooling_days", "earliest_eligible_exam_date"],
}


def parse_date(value: str) -> date:
    return date.fromisoformat(str(value).strip())


def add_months(d: date, months: int) -> date:
    month_index = d.month - 1 + months
    year = d.year + month_index // 12
    month = month_index % 12 + 1
    return date(year, month, min(d.day, calendar.monthrange(year, month)[1]))


def rounded_percent(correct, total) -> int:
    try:
        denominator = Decimal(str(total))
        numerator = Decimal(str(correct))
    except InvalidOperation as exc:
        raise ValueError("Score values must be numeric") from exc
    if denominator <= 0:
        raise ValueError("A score total must be greater than zero")
    if numerator < 0:
        raise ValueError("A score cannot be negative")
    value = numerator * Decimal("100") / denominator
    return int(value.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing input file: {path}")
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError(f"CSV has no header: {path}")
        return list(reader)


def write_csv(path: Path, columns: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    print(f"Created {path} ({len(rows)} rows)")


class ExamEngine:
    """Command-file-driven amateur radio examination scheduling engine."""

    def __init__(self, data_dir: Path | str | None = None, output_dir: Path | str | None = None):
        self.data_dir = Path(data_dir) if data_dir is not None else DATA
        self.output_dir = Path(output_dir) if output_dir is not None else OUTPUTS
        self.applicants: dict[str, dict] = {}
        self.sessions: dict[str, dict] = {}
        self.past: dict[str, list[dict]] = defaultdict(list)
        self.scores: dict[tuple[str, str], dict[str, dict]] = defaultdict(dict)
        self.allotments: dict[str, list[str]] = defaultdict(list)
        self.cycle_results: dict[str, list[dict]] = defaultdict(list)
        self.apply_log: list[dict] = []
        self.seating_rows: list[dict] = []
        self.result_rows: list[dict] = []
        self.reattempt_rows: list[dict] = []
        self.current_batch: str | None = None
        self.batch_date: date | None = None
        self.batch_queue: list[dict] = []
        self._printed_seating: set[str] = set()
        self._graded_sessions: set[str] = set()

    def _input_path(self, filename: str) -> Path:
        path = Path(filename)
        if path.is_absolute():
            raise ValueError("Input filenames must be relative to the data directory")
        resolved = (self.data_dir / path).resolve()
        if self.data_dir.resolve() not in resolved.parents:
            raise ValueError("Input filename must remain inside the data directory")
        return resolved

    def load_applicants(self, filename="applicants.csv"):
        rows = read_csv(self._input_path(filename))
        loaded = {}
        for row in rows:
            applicant_id = row["applicant_id"].strip()
            if not applicant_id or applicant_id in loaded:
                raise ValueError(f"Blank or duplicate applicant_id: {applicant_id!r}")
            parse_date(row["date_of_birth"])
            years = int(row.get("prior_licence_years") or 0)
            if years < 0:
                raise ValueError(f"Negative prior_licence_years for {applicant_id}")
            loaded[applicant_id] = row
        self.applicants = loaded

    def load_past_results(self, filename="past_results.csv"):
        self.past.clear()
        for row in read_csv(self._input_path(filename)):
            applicant_id = row["applicant_id"].strip()
            if applicant_id not in self.applicants:
                raise ValueError(f"Past result references unknown applicant {applicant_id}")
            parse_date(row["exam_date"])
            self.past[applicant_id].append(row)

    def load_sessions(self, filename="sessions.csv"):
        loaded = {}
        for row in read_csv(self._input_path(filename)):
            sid = row["session_id"].strip()
            if not sid or sid in loaded:
                raise ValueError(f"Blank or duplicate session_id: {sid!r}")
            row["_date"] = parse_date(row["exam_date"])
            seats = int(row["seats"])
            if seats < 0:
                raise ValueError(f"Negative seat count for {sid}")
            if row["grade_offered"] not in {"RESTRICTED", "GENERAL"}:
                raise ValueError(f"Invalid grade for session {sid}")
            row["_seats_used"] = 0
            loaded[sid] = row
        self.sessions = loaded

    def load_scores(self, filename="scores.csv"):
        self.scores.clear()
        for row in read_csv(self._input_path(filename)):
            sid, applicant_id = row["session_id"].strip(), row["applicant_id"].strip()
            section = row["section"].strip().upper()
            if sid not in self.sessions:
                raise ValueError(f"Score references unknown session {sid}")
            if applicant_id not in self.applicants:
                raise ValueError(f"Score references unknown applicant {applicant_id}")
            if section not in {"THEORY", "RULES", "MORSE"}:
                raise ValueError(f"Invalid score section {section}")
            key = (sid, applicant_id)
            if section in self.scores[key]:
                raise ValueError(f"Duplicate {section} score for {applicant_id} in {sid}")
            self.scores[key][section] = row

    def history(self, applicant_id: str, as_of: date | None = None) -> list[dict]:
        items = list(self.past[applicant_id]) + list(self.cycle_results[applicant_id])
        if as_of is not None:
            items = [r for r in items if parse_date(r["exam_date"]) <= as_of]
        return sorted(items, key=lambda row: parse_date(row["exam_date"]))

    def absence_count(self, applicant_id: str, as_of: date | None = None) -> int:
        return sum(
            1 for row in self.history(applicant_id, as_of)
            if row.get("overall_result") == "ABSENT"
            or any(row.get(field) == "ABSENT" for field in ("theory_result", "rules_result", "morse_result"))
        )

    def has_restricted_pass(self, applicant_id: str, as_of: date | None = None) -> bool:
        return any(
            row.get("grade") == "RESTRICTED" and row.get("overall_result") == "PASS"
            for row in self.history(applicant_id, as_of)
        )

    def failure_state(self, applicant_id: str, grade: str, as_of: date | None = None):
        rows = [r for r in self.history(applicant_id, as_of) if r.get("grade") == grade]
        rows.sort(key=lambda row: parse_date(row["exam_date"]), reverse=True)
        streak = 0
        latest_fail = None
        for row in rows:
            outcome = row.get("overall_result", "")
            if outcome == "ABSENT":
                continue
            if outcome == "FAIL":
                streak += 1
                if latest_fail is None:
                    latest_fail = parse_date(row["exam_date"])
            elif outcome == "PASS":
                break
        return latest_fail, streak

    def has_future_allotment(self, applicant_id: str, after_date: date) -> bool:
        return any(
            self.sessions[sid]["_date"] > after_date and applicant_id in people
            for sid, people in self.allotments.items()
        )

    def eligible_sections(self, applicant_id: str, grade: str, exam_date: date) -> set[str]:
        carried = set()
        for row in self.history(applicant_id, exam_date):
            if row.get("grade") != grade:
                continue
            passed_date = parse_date(row["exam_date"])
            if exam_date <= add_months(passed_date, 12):
                for section, field in (("THEORY", "theory_result"), ("RULES", "rules_result"), ("MORSE", "morse_result")):
                    if row.get(field) == "PASS":
                        carried.add(section)
        return carried

    def apply(self, line_no: int, applicant_id: str, grade: str, timestamp: str):
        grade = grade.strip().upper()
        entry = {
            "line_no": line_no, "batch_id": self.current_batch, "applicant_id": applicant_id,
            "grade": grade, "decision": "REJECTED", "session_id": "", "reason": "NONE"
        }
        if applicant_id not in self.applicants:
            entry["reason"] = "UNKNOWN_APPLICANT"
            self.apply_log.append(entry)
            return
        if grade not in {"RESTRICTED", "GENERAL"}:
            entry["reason"] = "GRADE_NOT_ELIGIBLE"
            self.apply_log.append(entry)
            return
        try:
            datetime.fromisoformat(timestamp.strip())
        except ValueError as exc:
            raise ValueError(f"Invalid application timestamp: {timestamp}") from exc
        if self.has_future_allotment(applicant_id, self.batch_date):
            entry["reason"] = "ALREADY_ALLOTTED"
            self.apply_log.append(entry)
            return
        applicant = self.applicants[applicant_id]
        if grade == "GENERAL":
            years = int(applicant.get("prior_licence_years", "0") or 0)
            if years < 1 and not self.has_restricted_pass(applicant_id, self.batch_date):
                entry["reason"] = "GRADE_NOT_ELIGIBLE"
                self.apply_log.append(entry)
                return
        latest_fail, streak = self.failure_state(applicant_id, grade, self.batch_date)
        cooling_days = 90 if streak >= 3 else 30
        earliest = date.fromordinal(latest_fail.toordinal() + cooling_days) if latest_fail else None
        self.batch_queue.append({
            "line_no": line_no, "entry": entry, "applicant_id": applicant_id,
            "grade": grade, "timestamp": timestamp,
            "low": self.absence_count(applicant_id, self.batch_date) >= 2,
            "earliest": earliest
        })

    def finish_batch(self, batch_id: str):
        if batch_id != self.current_batch:
            raise ValueError(f"BATCH_END {batch_id} does not match active batch {self.current_batch}")
        ordered = [q for q in self.batch_queue if not q["low"]] + [q for q in self.batch_queue if q["low"]]
        assigned_in_batch: set[str] = set()
        for q in ordered:
            entry = q["entry"]
            applicant_id = q["applicant_id"]
            if applicant_id in assigned_in_batch or self.has_future_allotment(applicant_id, self.batch_date):
                entry["reason"] = "ALREADY_ALLOTTED"
                self.apply_log.append(entry)
                continue
            applicant = self.applicants[applicant_id]
            candidates = sorted(
                (s for s in self.sessions.values()
                 if s["grade_offered"] == q["grade"] and s["_date"] > self.batch_date),
                key=lambda session: session["_date"]
            )
            if not candidates:
                entry["reason"] = "NO_SEATS"
                self.apply_log.append(entry)
                continue
            dob = parse_date(applicant["date_of_birth"])
            age_eligible = []
            cooling_eligible = []
            for session in candidates:
                exam_date = session["_date"]
                age = exam_date.year - dob.year - ((exam_date.month, exam_date.day) < (dob.month, dob.day))
                if age >= 12:
                    age_eligible.append(session)
                    if q["earliest"] is None or exam_date >= q["earliest"]:
                        cooling_eligible.append(session)
            if not age_eligible:
                entry["reason"] = "UNDER_AGE"
            elif not cooling_eligible:
                entry["reason"] = "COOLING_PERIOD"
            else:
                chosen = next((s for s in cooling_eligible if s["_seats_used"] < int(s["seats"])), None)
                if chosen is None:
                    entry["reason"] = "NO_SEATS"
                else:
                    chosen["_seats_used"] += 1
                    self.allotments[chosen["session_id"]].append(applicant_id)
                    assigned_in_batch.add(applicant_id)
                    entry["decision"] = "ALLOTTED"
                    entry["session_id"] = chosen["session_id"]
                    entry["reason"] = "LOW_PRIORITY" if q["low"] else "NONE"
            self.apply_log.append(entry)
        self.batch_queue = []
        self.current_batch = None
        self.batch_date = None

    def print_seating(self, session_id: str):
        if session_id not in self.sessions:
            raise ValueError(f"Unknown session {session_id}")
        if session_id in self._printed_seating:
            return
        session = self.sessions[session_id]
        for seat_no, applicant_id in enumerate(self.allotments[session_id], start=1):
            applicant = self.applicants[applicant_id]
            self.seating_rows.append({
                "session_id": session_id, "exam_date": session["exam_date"], "seat_no": seat_no,
                "applicant_id": applicant_id, "applicant_name": applicant["applicant_name"],
                "grade": session["grade_offered"],
                "priority": "LOW" if self.absence_count(applicant_id, session["_date"]) >= 2 else "NORMAL"
            })
        self._printed_seating.add(session_id)

    def grade_section(self, section: str, score_rows: dict, carried: set[str], pass_mark: int):
        if section in carried:
            return "NONE", "EXEMPT"
        if section not in score_rows:
            return "NONE", "FAIL"
        row = score_rows[section]
        pct = rounded_percent(row["correct"], row["total"])
        if Decimal(str(row["correct"])) > Decimal(str(row["total"])):
            raise ValueError(f"{section} correct marks exceed total marks")
        return str(pct), "PASS" if pct >= pass_mark else "FAIL"

    def grade_session(self, session_id: str):
        if session_id not in self.sessions:
            raise ValueError(f"Unknown session {session_id}")
        if session_id in self._graded_sessions:
            return
        session = self.sessions[session_id]
        exam_date, grade = session["_date"], session["grade_offered"]
        for applicant_id in sorted(self.allotments[session_id]):
            score_rows = self.scores.get((session_id, applicant_id), {})
            carried = self.eligible_sections(applicant_id, grade, exam_date)
            if not score_rows:
                theory_pct = rules_pct = morse_wpm = "NONE"
                theory_result = rules_result = "ABSENT"
                morse_result = "ABSENT" if grade == "GENERAL" else "NA"
                overall = "ABSENT"
            else:
                threshold = 50 if grade == "RESTRICTED" else 60
                theory_pct, theory_result = self.grade_section("THEORY", score_rows, carried, threshold)
                rules_pct, rules_result = self.grade_section("RULES", score_rows, carried, threshold)
                if grade == "GENERAL":
                    if "MORSE" in carried:
                        morse_wpm, morse_result = "NONE", "EXEMPT"
                    elif "MORSE" in score_rows:
                        morse_wpm = str(score_rows["MORSE"]["correct"])
                        morse_result = "PASS" if Decimal(morse_wpm) >= 5 else "FAIL"
                    else:
                        morse_wpm, morse_result = "NONE", "FAIL"
                else:
                    morse_wpm, morse_result = "NONE", "NA"
                outcomes = [theory_result, rules_result] + ([morse_result] if grade == "GENERAL" else [])
                overall = "PASS" if all(outcome in {"PASS", "EXEMPT"} for outcome in outcomes) else "FAIL"
            result = {
                "session_id": session_id, "applicant_id": applicant_id, "grade": grade,
                "theory_pct": theory_pct, "theory_result": theory_result,
                "rules_pct": rules_pct, "rules_result": rules_result,
                "morse_wpm": morse_wpm, "morse_result": morse_result,
                "overall_result": overall
            }
            self.result_rows.append(result)
            history_row = dict(result)
            history_row["exam_date"] = session["exam_date"]
            self.cycle_results[applicant_id].append(history_row)
        self._graded_sessions.add(session_id)

    def print_reattempt(self, as_of_date: str):
        as_of = parse_date(as_of_date)
        rows_out = []
        for applicant_id in sorted(self.applicants):
            history = self.history(applicant_id, as_of)
            if not history:
                continue
            latest = history[-1]
            if latest.get("overall_result") != "FAIL":
                continue
            grade = latest["grade"]
            last_date, streak = self.failure_state(applicant_id, grade, as_of)
            if last_date is None:
                continue
            cooling = 90 if streak >= 3 else 30
            earliest = date.fromordinal(last_date.toordinal() + cooling)
            rows_out.append({
                "applicant_id": applicant_id, "grade": grade,
                "last_exam_date": last_date.isoformat(), "consecutive_failures": streak,
                "cooling_days": cooling, "earliest_eligible_exam_date": earliest.isoformat()
            })
        self.reattempt_rows = rows_out

    def _write_outputs(self):
        write_csv(self.output_dir / "apply_log.csv", OUTPUT_COLUMNS["apply_log.csv"],
                  sorted(self.apply_log, key=lambda row: int(row["line_no"])))
        write_csv(self.output_dir / "seating.csv", OUTPUT_COLUMNS["seating.csv"], self.seating_rows)
        write_csv(self.output_dir / "results.csv", OUTPUT_COLUMNS["results.csv"], self.result_rows)
        write_csv(self.output_dir / "reattempt.csv", OUTPUT_COLUMNS["reattempt.csv"], self.reattempt_rows)

    def run(self, command_file="commands.txt"):
        command_path = self._input_path(command_file)
        with command_path.open("r", encoding="utf-8-sig") as handle:
            lines = list(handle)
        for line_no, raw in enumerate(lines, start=1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            parts = [part.strip() for part in line.split("|")]
            command, args = parts[0], parts[1:]
            try:
                if command == "LOAD_APPLICANTS" and len(args) == 1:
                    self.load_applicants(args[0])
                elif command == "LOAD_PAST_RESULTS" and len(args) == 1:
                    self.load_past_results(args[0])
                elif command == "LOAD_SESSIONS" and len(args) == 1:
                    self.load_sessions(args[0])
                elif command == "LOAD_SCORES" and len(args) == 1:
                    self.load_scores(args[0])
                elif command == "BATCH_START" and len(args) == 2:
                    if self.current_batch is not None:
                        raise ValueError("A batch is already active")
                    self.current_batch, self.batch_date = args[0], parse_date(args[1])
                    self.batch_queue = []
                elif command == "APPLY" and len(args) == 3:
                    if self.current_batch is None:
                        raise ValueError("APPLY used outside a batch")
                    self.apply(line_no, args[0], args[1], args[2])
                elif command == "BATCH_END" and len(args) == 1:
                    self.finish_batch(args[0])
                elif command == "PRINT_SEATING" and len(args) == 1:
                    self.print_seating(args[0])
                elif command == "GRADE" and len(args) == 1:
                    self.grade_session(args[0])
                elif command == "PRINT_RESULTS" and len(args) == 1:
                    # Result rows are persisted together at the end of the command stream.
                    if args[0] not in self.sessions:
                        raise ValueError(f"Unknown session {args[0]}")
                elif command == "PRINT_REATTEMPT" and len(args) == 1:
                    self.print_reattempt(args[0])
                else:
                    raise ValueError(f"Unknown command or invalid arguments: {command}")
            except Exception as exc:
                raise RuntimeError(f"Error on commands.txt line {line_no}: {line}: {exc}") from exc
        if self.current_batch is not None:
            raise RuntimeError(f"Unclosed batch: {self.current_batch}")
        self._write_outputs()


def main():
    parser = argparse.ArgumentParser(description="ECE-061 Amateur Radio Exam Scheduling and Result Engine")
    parser.add_argument("--commands", default="commands.txt", help="Command file located inside data/")
    parser.add_argument("--data-dir", default=str(DATA))
    parser.add_argument("--output-dir", default=str(OUTPUTS))
    args = parser.parse_args()
    ExamEngine(args.data_dir, args.output_dir).run(args.commands)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
