# 🤖 Autonomous Insurance Claims Processing Agent

An AI-powered FNOL (First Notice of Loss) processing agent that ingests insurance claim
documents (PDF/TXT), extracts structured data, validates mandatory fields, classifies the
claim, and recommends the appropriate routing workflow — with human-readable reasoning.

## ✨ Features

- 📄 **Document ingestion** — PDF + TXT, with OCR fallback for scanned PDFs
- 🧠 **Hybrid extraction** — regex + spaCy NER for robust field extraction
- ✅ **Validation** — detects missing mandatory fields
- 🚦 **Rule-based routing** — Fast-track, Manual Review, Investigation Flag, Specialist Queue
- 💬 **AI reasoning** — explains every routing decision in plain language
- 🌐 **REST API** — FastAPI with auto-generated Swagger docs
- 🖥️ **Dashboard** — Streamlit UI to upload and inspect claims
- ☁️ **Azure-ready** — Blob Storage integration placeholders
- 🐳 **Dockerized** — single command to run

## 🧱 Tech Stack

| Layer    | Tools                                       |
|----------|---------------------------------------------|
| Backend  | Python 3.11, FastAPI, Pydantic              |
| AI/NLP   | spaCy, transformers, regex                  |
| PDF/OCR  | pdfplumber, PyPDF2, pytesseract, pdf2image  |
| Frontend | Streamlit                                   |
| Cloud    | Azure Blob Storage (optional)               |
| Tests    | pytest, httpx                               |

## 📁 Project Structure

```
insurance-claims-agent/
├── app/
│   ├── main.py          # FastAPI app & /process-claim endpoint
│   ├── extractor.py     # Regex + spaCy field extraction
│   ├── validator.py     # Mandatory-field validation
│   ├── router.py        # Routing rules engine
│   ├── reasoning.py     # Human-readable explanation builder
│   ├── utils.py         # PDF/TXT/OCR + Azure Blob helpers
│   └── schemas.py       # Pydantic models
├── frontend/
│   └── streamlit_app.py # Streamlit dashboard
├── sample_documents/    # Example FNOL claim files
├── tests/               # pytest suite
├── requirements.txt
├── Dockerfile
├── .env.example
└── README.md
```

## 🚀 Setup

```bash
# 1. Clone and enter the project
cd insurance-claims-agent

# 2. Create venv & install deps
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 3. (Optional) Download spaCy English model for better NER
python -m spacy download en_core_web_sm

# 4. (Optional) System packages for OCR
#   - macOS:  brew install tesseract poppler
#   - Ubuntu: sudo apt install tesseract-ocr poppler-utils

# 5. Copy env file
cp .env.example .env
```

## ▶️ Run Locally

**Terminal 1 — API:**
```bash
uvicorn app.main:app --reload --port 8000
```
Swagger UI → <http://localhost:8000/docs>

**Terminal 2 — Streamlit dashboard:**
```bash
streamlit run frontend/streamlit_app.py
```
Dashboard → <http://localhost:8501>

## 🐳 Run with Docker

```bash
docker build -t claims-agent .
docker run -p 8000:8000 --env-file .env claims-agent
```

## 🔌 API Usage

### `POST /process-claim`

Multipart upload with a single `file` field (PDF or TXT).

```bash
curl -X POST http://localhost:8000/process-claim \
     -F "file=@sample_documents/sample_claim.txt"
```

### Example JSON response

```json
{
  "extractedFields": {
    "policy": {
      "policy_number": "AUTO-998877-21",
      "policyholder_name": "John A. Smith",
      "effective_date_from": "01/15/2024",
      "effective_date_to": "01/15/2025"
    },
    "incident": {
      "date": "04/22/2025",
      "time": "14:30",
      "location": "5th Avenue & Main St, Springfield, IL",
      "description": "Insured vehicle was rear-ended at a traffic light..."
    },
    "parties": [
      {"name": "John A. Smith", "role": "claimant", "contact": "(555) 123-4567"},
      {"name": "Mary Johnson", "role": "third_party", "contact": null}
    ],
    "asset": {
      "asset_type": "vehicle",
      "asset_id": "4T1BF1FK5HU123456",
      "estimated_damage": 4500.0
    },
    "claim_type": "collision",
    "attachments": ["police_report.pdf", "damage_photos.zip"],
    "initial_estimate": 4500.0
  },
  "missingFields": [],
  "recommendedRoute": "Fast-track",
  "reasoning": "Recommended route: Fast-track. Decision drivers: Estimated damage $4,500.00 is below $25,000 threshold. Reported estimated damage is $4,500.00. Claim type identified as 'collision'. All mandatory fields are present."
}
```

## 🧪 Tests

```bash
pytest -v
```

## 🚦 Routing Rules (priority order)

1. **Investigation Flag** — description contains `fraud`, `inconsistent`, or `staged`
2. **Specialist Queue** — `claim_type == "injury"`
3. **Manual Review** — any mandatory field missing
4. **Fast-track** — `estimated_damage < 25,000`
5. Default → **Manual Review**

## ☁️ Azure Integration

Set `AZURE_STORAGE_CONNECTION_STRING` in `.env` to automatically archive every uploaded
document into the configured Blob container. The placeholder hook lives in
`app/utils.py::upload_to_azure_blob` — extend it with Form Recognizer, Azure OpenAI, or
Cognitive Services as needed.

## 🔮 Future Improvements

- Replace regex with an LLM (Azure OpenAI / GPT-4) for higher recall on freeform PDFs
- Use Azure AI Document Intelligence (Form Recognizer) for ACORD form templates
- Persist claims & decisions in PostgreSQL / Cosmos DB
- Auth (Azure AD), role-based access, audit logging
- Async job queue (Azure Service Bus) for high-volume ingestion
- Front-end claim review & override workflow
- Continuous fraud-detection model trained on historical claims

---

Built as an educational, production-style reference project. PRs welcome.
