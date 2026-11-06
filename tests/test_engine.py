import csv
import shutil
import sys
from datetime import date
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))
from main import ExamEngine, add_months, rounded_percent


def load_real_project(tmp_path):
    data_dir = tmp_path / "data"
    shutil.copytree(PROJECT_ROOT / "data", data_dir)
    output_dir = tmp_path / "outputs"
    engine = ExamEngine(data_dir=data_dir, output_dir=output_dir)
    engine.run("commands.txt")
    return engine, output_dir


def read_rows(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_round_half_up_boundaries():
    assert rounded_percent("59.5", "100") == 60
    assert rounded_percent("24.5", "49") == 50
    assert rounded_percent("24", "49") == 49


def test_zero_or_negative_total_is_rejected():
    with pytest.raises(ValueError):
        rounded_percent(1, 0)
    with pytest.raises(ValueError):
        rounded_percent(1, -2)


def test_add_months_clamps_month_end():
    assert add_months(date(2025, 1, 31), 1) == date(2025, 2, 28)
    assert add_months(date(2024, 2, 29), 12) == date(2025, 2, 28)


def test_full_sample_run_and_exact_output_schemas(tmp_path):
    _, output_dir = load_real_project(tmp_path)
    expected = {
        "apply_log.csv": (82, ["line_no", "batch_id", "applicant_id", "grade", "decision", "session_id", "reason"]),
        "seating.csv": (78, ["session_id", "exam_date", "seat_no", "applicant_id", "applicant_name", "grade", "priority"]),
        "results.csv": (78, ["session_id", "applicant_id", "grade", "theory_pct", "theory_result", "rules_pct", "rules_result", "morse_wpm", "morse_result", "overall_result"]),
        "reattempt.csv": (21, ["applicant_id", "grade", "last_exam_date", "consecutive_failures", "cooling_days", "earliest_eligible_exam_date"]),
    }
    for filename, (count, columns) in expected.items():
        with (output_dir / filename).open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            assert reader.fieldnames == columns
            assert len(list(reader)) == count


def test_age_is_checked_on_each_candidate_exam_date(tmp_path):
    _, output_dir = load_real_project(tmp_path)
    rows = read_rows(output_dir / "apply_log.csv")
    app008 = next(row for row in rows if row["applicant_id"] == "APP-008")
    app071 = next(row for row in rows if row["applicant_id"] == "APP-071")
    assert (app008["decision"], app008["session_id"]) == ("ALLOTTED", "SES-03")
    assert (app071["decision"], app071["session_id"]) == ("ALLOTTED", "SES-01")


def test_grade_eligibility_and_existing_allotment(tmp_path):
    _, output_dir = load_real_project(tmp_path)
    rows = read_rows(output_dir / "apply_log.csv")
    def get(applicant_id, batch):
        return next(r for r in rows if r["applicant_id"] == applicant_id and r["batch_id"] == batch)
    assert get("APP-052", "B1")["reason"] == "GRADE_NOT_ELIGIBLE"
    assert get("APP-040", "B1")["decision"] == "ALLOTTED"
    assert get("APP-038", "B2")["reason"] == "ALREADY_ALLOTTED"
    # APP-015 is not forced into full SES-03; the later assigned sitting is outside the exemption window.
    app015 = get("APP-015", "B2")
    assert app015["session_id"] == "SES-05"


def test_unknown_applicant_does_not_get_a_seat(tmp_path):
    _, output_dir = load_real_project(tmp_path)
    rows = read_rows(output_dir / "apply_log.csv")
    unknown = next(r for r in rows if r["applicant_id"] == "APP-099")
    assert unknown["decision"] == "REJECTED"
    assert unknown["reason"] == "UNKNOWN_APPLICANT"
    assert unknown["session_id"] == ""


def test_absence_priority_and_seat_capacity_order(tmp_path):
    _, output_dir = load_real_project(tmp_path)
    apply_rows = read_rows(output_dir / "apply_log.csv")
    low = next(r for r in apply_rows if r["applicant_id"] == "APP-007" and r["batch_id"] == "B2")
    assert low["session_id"] == "SES-05"
    assert low["reason"] == "LOW_PRIORITY"
    seating = read_rows(output_dir / "seating.csv")
    low_seat = next(r for r in seating if r["applicant_id"] == "APP-007" and r["session_id"] == "SES-05")
    assert low_seat["priority"] == "LOW"
    # The tenth normal GENERAL application fills SES-02; APP-036 rolls to SES-04.
    app036 = next(r for r in apply_rows if r["applicant_id"] == "APP-036")
    assert app036["session_id"] == "SES-04"


def test_cooling_periods_and_exact_day_30_allotment(tmp_path):
    _, output_dir = load_real_project(tmp_path)
    apply_rows = read_rows(output_dir / "apply_log.csv")
    app050 = next(r for r in apply_rows if r["applicant_id"] == "APP-050" and r["batch_id"] == "B3")
    app056 = next(r for r in apply_rows if r["applicant_id"] == "APP-056" and r["batch_id"] == "B2")
    app064 = next(r for r in apply_rows if r["applicant_id"] == "APP-064" and r["batch_id"] == "B2")
    assert app050["session_id"] == "SES-05"  # 30 days after 2026-11-13
    assert (app056["decision"], app056["reason"]) == ("REJECTED", "COOLING_PERIOD")
    assert app064["session_id"] == "SES-06"  # SES-04 is only 28 days after failure
    reattempt = read_rows(output_dir / "reattempt.csv")
    app056_report = next(r for r in reattempt if r["applicant_id"] == "APP-056")
    assert app056_report["consecutive_failures"] == "3"
    assert app056_report["cooling_days"] == "90"
    assert app056_report["earliest_eligible_exam_date"] == "2027-01-12"


def test_section_pass_mark_rounding_and_morse(tmp_path):
    _, output_dir = load_real_project(tmp_path)
    results = read_rows(output_dir / "results.csv")
    def result(applicant_id, session_id):
        return next(r for r in results if r["applicant_id"] == applicant_id and r["session_id"] == session_id)
    assert result("APP-037", "SES-01")["rules_result"] == "PASS"
    assert result("APP-037", "SES-01")["rules_pct"] == "50"
    assert result("APP-049", "SES-01")["rules_result"] == "FAIL"
    assert result("APP-049", "SES-01")["rules_pct"] == "49"
    assert result("APP-001", "SES-04")["theory_result"] == "PASS"
    assert result("APP-001", "SES-04")["theory_pct"] == "60"
    assert result("APP-010", "SES-02")["morse_result"] == "FAIL"
    assert result("APP-010", "SES-02")["overall_result"] == "FAIL"
    # APP-015's intended exact-12-month scenario is not reached in this command sequence.
    app015 = result("APP-015", "SES-05")
    assert app015["theory_result"] == "ABSENT"
    assert app015["overall_result"] == "ABSENT"


def test_exact_12_month_exemption_and_one_day_expiry():
    engine = ExamEngine()
    engine.past["APP-015"].append({
        "applicant_id": "APP-015", "exam_date": "2025-11-13", "grade": "RESTRICTED",
        "theory_result": "PASS", "rules_result": "FAIL", "morse_result": "NA",
        "overall_result": "FAIL"
    })
    assert "THEORY" in engine.eligible_sections("APP-015", "RESTRICTED", date(2026, 11, 13))
    assert "THEORY" not in engine.eligible_sections("APP-015", "RESTRICTED", date(2026, 11, 14))


def test_more_than_12_months_old_pass_is_not_exempt():
    engine = ExamEngine()
    engine.past["APP-043"].append({
        "applicant_id": "APP-043", "exam_date": "2025-11-12", "grade": "RESTRICTED",
        "theory_result": "PASS", "rules_result": "FAIL", "morse_result": "NA",
        "overall_result": "FAIL"
    })
    assert "THEORY" not in engine.eligible_sections("APP-043", "RESTRICTED", date(2026, 11, 13))


def test_duplicate_applications_in_one_batch_only_allocate_once():
    engine = ExamEngine()
    engine.applicants["APP-1"] = {
        "applicant_id": "APP-1", "applicant_name": "Test Applicant",
        "date_of_birth": "2000-01-01", "prior_licence_years": "0"
    }
    engine.sessions["SES-1"] = {
        "session_id": "SES-1", "exam_date": "2026-10-14",
        "_date": date(2026, 10, 14), "_seats_used": 0,
        "seats": "2", "grade_offered": "RESTRICTED"
    }
    engine.current_batch = "B1"
    engine.batch_date = date(2026, 9, 25)
    engine.apply(1, "APP-1", "RESTRICTED", "2026-09-25 10:00:00")
    engine.apply(2, "APP-1", "RESTRICTED", "2026-09-25 10:01:00")
    engine.finish_batch("B1")
    assert engine.allotments["SES-1"] == ["APP-1"]
    assert sorted(r["reason"] for r in engine.apply_log) == ["ALREADY_ALLOTTED", "NONE"]


def test_reattempt_report_respects_as_of_date():
    engine = ExamEngine()
    engine.applicants["APP-1"] = {"applicant_id": "APP-1"}
    engine.cycle_results["APP-1"].append({
        "exam_date": "2026-03-01", "grade": "RESTRICTED", "overall_result": "FAIL"
    })
    engine.print_reattempt("2026-02-28")
    assert engine.reattempt_rows == []
    engine.print_reattempt("2026-03-01")
    assert len(engine.reattempt_rows) == 1
