# NJ Change Manager Assistant

A specialized release intelligence and regulatory compliance tracking workspace built with **Python**, **FastAPI**, and **Streamlit** to streamline release workflows under **New Jersey Division of Gaming Enforcement (DGE)** compliance rules.

---

## Key Capabilities
- **Automated Release Aggregation:** Fetches Jira release metadata, linked child issues, and compliance mappings (`[RN]`, `[ND]`, `[EX]`) via FastAPI.
- **Compliance Policy Engine:** Automatically classifies changes into regulatory workflows (`3-Day Wait Rule`, `Notify & Execute`, or `No Wait`).
- **ID Extraction & Manifest Parsing:** Extracts unique issue keys from unstructured release notes and Confluence/Wiki manifests.
- **Interactive Dashboard & Email Generator:** Streamlit UI for release monitoring, dependency verification, and regulator communication prep.

---

## Tech Stack
- **Backend:** FastAPI, Uvicorn, Pydantic, Python-Jira
- **Frontend:** Streamlit, Pandas
- **OCR & Parsing:** EasyOCR, Pillow, BeautifulSoup4
- **Testing & CI/CD:** Pytest, FastAPI TestClient, Ruff, GitHub Actions

---

## Project Structure
```text
├── .github/workflows/
│   └── ci.yml             # Automated Ruff linting & Pytest unit test pipeline
├── tests/
│   └── test_main.py       # Unit & API endpoint tests with mocked Jira integrations
├── app.py                 # Streamlit multi-tab frontend workspace
├── main.py                # FastAPI backend service & compliance classification logic
└── requirements.txt       # Project dependencies
```

---

## Local Setup & Execution

### 1. Clone & create a virtual environment
```bash
git clone [https://github.com/AnaVauquelin/change-manager-assistant.git](https://github.com/AnaVauquelin/change-manager-assistant.git)
cd change-manager-assistant
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure environment variables
Create a `.env` file in the project root:
```env
JIRA_SERVER="[https://your-jira-instance.atlassian.net](https://your-jira-instance.atlassian.net)"
JIRA_API_TOKEN="your_personal_access_token"
```

### 3. Run the backend & frontend
```bash
# Terminal 1: Start FastAPI backend
python3 main.py

# Terminal 2: Start Streamlit UI
streamlit run app.py
```

### 4. Run unit tests
```bash
pytest -v
```
