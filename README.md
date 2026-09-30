# TestIQ – AI-Powered Software Testing & Intelligent Automation Platform

[![Python](https://img.shields.io/badge/Python-3.12%2B-blue)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35-red)](https://streamlit.io)
[![SQLite](https://img.shields.io/badge/Database-SQLite-green)](https://sqlite.org)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

---

## 📌 Project Overview

**TestIQ** is a full-stack Python application that transforms natural-language
software requirements into structured, executable test cases — complete with
automated validation, defect analysis, and a professional testing dashboard.

It is designed as a final-year engineering portfolio project demonstrating
skills directly relevant to an **Associate Software Test Engineer /
Intelligent Automation** role.

---

## 🎯 Problem Statement

Software teams spend significant time manually writing test cases from
requirement documents. Test coverage is often incomplete, boundary conditions
are missed, and defect tracking is disconnected from test results.

**TestIQ solves this by:**

1. Automatically analysing software requirements
2. Generating structured positive, negative, boundary, and validation test cases
3. Executing tests against a real Python validation engine
4. Detecting and classifying defects from failures
5. Visualising quality metrics on an interactive dashboard
6. Exporting reports for documentation

---

## ✨ Features

| Feature | Description |
|---|---|
| Requirement Analysis | Detects fields, validation rules, edge cases, and risks |
| Test Case Generation | Positive / Negative / Boundary / Validation test cases |
| Automated Execution | Real validation engine – no hard-coded PASS/FAIL |
| Defect Detection | Auto-creates defect records from failed tests |
| Defect Classification | Rule-based severity (Critical/Major/Minor/Trivial) |
| Interactive Dashboard | Plotly charts, Streamlit metrics |
| Report Export | CSV and text reports |
| AI Enhancement | Optional OpenAI/Gemini integration |
| Offline Mode | Fully functional without any API key |

---

## 🏗️ System Architecture

```
User Input
    ↓
Streamlit UI (app.py)
    ↓
Requirement Analyzer (requirement_analyzer.py)
    ↓
AI / Rule-Based Engine (ai_engine.py)
    ↓
Test Case Generator (test_generator.py)
    ↓
Test Execution Engine (test_executor.py)
    ↓
Validation Engine (validators.py)
    ↓
Defect Analyzer (bug_analyzer.py)
    ↓
SQLite Database (database.py)
    ↓
Dashboard & Reports (app.py + report_generator.py)
```

---

## 🛠️ Technology Stack

| Technology | Purpose |
|---|---|
| Python 3.12+ | Core language |
| Streamlit 1.35 | Web UI framework |
| SQLite | Persistent data storage |
| Pandas | Data manipulation |
| Plotly | Interactive charts |
| python-dotenv | Environment variable management |
| pytest | Unit testing |

---

## 📁 Project Structure

```
TestIQ/
│
├── app.py                   # Streamlit multi-page application
├── config.py                # Central configuration
├── database.py              # SQLite CRUD layer
├── requirement_analyzer.py  # Rule-based requirement analysis
├── ai_engine.py             # AI abstraction layer
├── test_generator.py        # Test case generation engine
├── test_executor.py         # Test execution engine
├── bug_analyzer.py          # Defect detection and classification
├── report_generator.py      # CSV / text report generation
├── validators.py            # Reusable input validators
├── utils.py                 # Shared utilities and helpers
│
├── data/
│   └── testiq.db            # SQLite database (auto-created)
│
├── reports/                 # Generated reports directory
│
├── tests/
│   ├── __init__.py
│   ├── test_validators.py   # Validator unit tests
│   ├── test_test_generator.py # Generator unit tests
│   └── test_executor.py     # Executor + defect unit tests
│
├── requirements.txt
├── .env.example
└── README.md
```

---

## ⚙️ Installation

### 1. Clone the repository

```bash
git clone https://github.com/your-username/TestIQ.git
cd TestIQ
```

### 2. Create a virtual environment (recommended)

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## 🔑 Environment Setup

```bash
cp .env.example .env
```

The application works **fully offline** without any API key.

To enable AI-enhanced analysis, edit `.env`:

```env
AI_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here
```

---

## ▶️ How to Run

```bash
streamlit run app.py
```

The application opens at **http://localhost:8501**

---

## 📖 How to Use

### Workflow

1. **Dashboard** – Review project metrics and charts
2. **Requirement Analysis** – Enter a software requirement (or load the sample)
3. **Test Case Generator** – Select a requirement and generate test cases
4. **Test Execution** – Run all tests or a single test
5. **Defect Analysis** – View auto-classified defects; update status
6. **Reports** – Download CSV or text summary

### Example Requirement

**Title:** User Registration

**Description:**
> Users should be able to register with a valid name, email address and password.

**Acceptance Criteria:**
```
- Name is required (minimum 2 characters)
- Email must contain a valid format (user@domain.tld)
- Password must be at least 8 characters
- Empty fields must be rejected
```

---

## 🧪 Testing

Run all unit tests:

```bash
pytest tests/ -v
```

Run a specific test file:

```bash
pytest tests/test_validators.py -v
pytest tests/test_test_generator.py -v
pytest tests/test_executor.py -v
```

Run with coverage (requires pytest-cov):

```bash
pip install pytest-cov
pytest tests/ --cov=. --cov-report=term-missing
```

---

## 📸 Screenshots

*(Add screenshots after running the application)*

- [ ] Dashboard with metrics and charts
- [ ] Requirement Analysis page
- [ ] Generated test cases (all types)
- [ ] Test execution results
- [ ] Defect list with severity badges
- [ ] CSV report download

---

## 🔄 Example Workflow

```
1. Open application → http://localhost:8501
2. Click "Requirement Analysis" in sidebar
3. Click "Load Sample Requirement"
4. Click "Analyse Requirement"
   → System extracts fields: name, email, password
   → Shows validation rules, edge cases, boundary conditions
5. Click "Test Case Generator"
   → Select requirement → Click "Generate Test Cases"
   → ~30 test cases created (Positive/Negative/Boundary/Validation)
6. Click "Test Execution"
   → Click "Run All Tests"
   → Validation engine produces real PASS/FAIL results
7. Click "Defect Analysis"
   → Failed tests automatically create classified defects
8. Click "Reports"
   → Download CSV exports
```

---

## 🔮 Future Enhancements

1. **Selenium Integration** – Execute UI test cases in a real browser
2. **UiPath / RPA Connector** – Export test cases as RPA workflows
3. **CI/CD Integration** – GitHub Actions pipeline for automated regression
4. **REST API** – Expose test generation as an API endpoint (FastAPI)
5. **JIRA Integration** – Push defects directly to JIRA
6. **Natural Language Processing** – Improved requirement parsing
7. **Test Coverage Metrics** – Requirement coverage heat maps
8. **Scheduled Execution** – Cron-based automated test runs
9. **User Authentication** – Multi-user support
10. **PDF Reports** – Professional PDF report generation

---

## ⚠️ Limitations

- Test execution validates input data strings, not a live application
- AI features require an external API key (application works without one)
- PDF report generation not included (CSV and text reports available)
- No live browser automation (Selenium integration is a future enhancement)
- SQLite is suitable for local development; production would use PostgreSQL

---

## 👤 Author

**TestIQ Portfolio Project**

Developed to demonstrate skills in:
- Software Testing (manual and automated)
- Test Case Design (positive, negative, boundary, validation)
- Python Programming (modular, clean, PEP 8)
- Defect Analysis and Classification
- Database Design (SQLite with parameterised queries)
- Web Application Development (Streamlit)
- AI-Assisted Testing Concepts
- Intelligent Automation Principles

---

## 📄 License

MIT License – free to use, modify, and distribute.
