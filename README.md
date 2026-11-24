# ECE-061 – Amateur Radio Licence Exam Scheduling and Result Engine

**Capstone Project | Team E036**

An automated examination management system developed using Python to handle applicant eligibility, examination scheduling, seat allotment, result processing, and reattempt eligibility for Amateur Radio Licence examinations.

[![Python](https://img.shields.io/badge/Python-3.x-blue?logo=python)](https://www.python.org/)
[![Testing](https://img.shields.io/badge/Testing-Pytest-green)](https://pytest.org/)
[![Repository](https://img.shields.io/badge/Repository-GitHub-black?logo=github)](https://github.com/shivarajp26/E036-ECE-061)

---

## 📌 Project Overview

The **Amateur Radio Licence Exam Scheduling and Result Engine** is designed to automate the examination workflow for amateur radio licence applicants.

The system processes applicant records, verifies eligibility, allocates examination seats, evaluates examination scores, applies exemption rules, and determines reattempt eligibility according to predefined business rules.

It uses CSV files as input and generates structured CSV output reports.

## 🎯 Project Objectives

- Automate applicant eligibility verification.
- Manage examination applications and batches.
- Allocate applicants to available examination sessions.
- Process examination scores and calculate results.
- Apply previous examination exemptions.
- Enforce reattempt cooling periods.
- Generate seating, result, and reattempt reports.

## ✨ Key Features

### 1. Applicant Management
- Load applicant information from CSV files.
- Validate applicant details.
- Check minimum age requirements.
- Verify eligibility for RESTRICTED and GENERAL grades.

### 2. Examination Scheduling
- Process applications in batches.
- Allocate applicants to the earliest eligible examination session.
- Manage available seat capacity.
- Maintain application order and priority.

### 3. Result Processing
- Calculate section-wise examination percentages.
- Apply the required passing criteria.
- Support half-up percentage rounding.
- Evaluate MORSE examination performance.

### 4. Exemption Management
- Carry forward previously passed sections within the permitted 12-month period.
- Apply exemptions only to the same examination grade.
- Avoid renewing exemption periods through already exempted sections.

### 5. Reattempt Management
- Enforce 30-day cooling periods after failures.
- Apply 90-day cooling periods after three consecutive failures.
- Track examination absences.
- Assign LOW priority after two absences.

### 6. Report Generation

The system generates the following reports:

| Output File | Description |
|---|---|
| `apply_log.csv` | Application decisions and allotment details |
| `seating.csv` | Examination seating arrangements |
| `results.csv` | Section-wise and overall examination results |
| `reattempt.csv` | Reattempt eligibility and cooling-period details |

## 🛠️ Technologies Used

| Technology | Purpose |
|---|---|
| Python 3 | Core application development |
| CSV | Input data and output report processing |
| Pytest | Automated testing |
| Git | Version control |
| GitHub | Source code hosting |

## 📂 Project Structure

```text
E036-ECE-061/
│
├── src/
│   └── main.py
│
├── tests/
│   └── test_engine.py
│
├── data/
│   ├── applicants.csv
│   ├── past_results.csv
│   ├── sessions.csv
│   ├── scores.csv
│   └── commands.txt
│
├── outputs/
│   ├── apply_log.csv
│   ├── seating.csv
│   ├── results.csv
│   └── reattempt.csv
│
├── README.md
└── requirements.txt
```

## ⚙️ Installation and Setup

### Prerequisites

- Python 3.x
- Visual Studio Code
- Git

### 1. Clone the Repository

```bash
git clone https://github.com/shivarajp26/E036-ECE-061.git
```

### 2. Navigate to the Project Folder

```bash
cd E036-ECE-061
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

## ▶️ Running the Project

From the project root directory, execute:

```bash
python .\src\main.py
```

The application reads the input data and command instructions, processes the examination workflow, and generates the output CSV reports inside the `outputs/` directory.

## 🧪 Running Tests

Run the automated test suite using:

```bash
python -m pytest -v
```

The tests verify important functionality, including:

- Percentage rounding.
- Applicant age and grade eligibility.
- Examination seat allotment.
- Application priority.
- Cooling-period calculations.
- Section-wise passing criteria.
- Exemption handling.
- Reattempt eligibility.

## 📋 Input Data Files

| File | Purpose |
|---|---|
| `applicants.csv` | Applicant registration details |
| `past_results.csv` | Previous examination results |
| `sessions.csv` | Examination session details and seat capacity |
| `scores.csv` | Applicant examination scores |
| `commands.txt` | Instructions for executing the examination workflow |

## 📤 Output Reports

All generated reports are stored in the `outputs/` directory.

- **Application Log:** Records application acceptance, rejection, and allotment decisions.
- **Seating Report:** Displays the applicants assigned to each examination session.
- **Results Report:** Contains section-wise scores and overall results.
- **Reattempt Report:** Displays previous failures, cooling periods, and earliest eligible reattempt dates.

## 👥 Project Team

**Team ID:** E036

| Team Member | Role |
|---|---|
| Shivaraj Patil | Project Team Member |
| Sindhu | Project Team Member |

## 🎥 Project Demonstration Video

Watch the project demonstration here:

[Click here to watch the project demonstration](https://drive.google.com/file/d/15-9nWEuFJE5ykthAxRu0n4Ps502qi99c/view?usp=drive_link)

---

**Developed as part of the Capstone Project – ECE-061.**