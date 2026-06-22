# RupeeRadar — Architecture Document

> **Version:** 1.0  
> **Based on:** docs/context.md, docs/problemStatement.txt

---

## 1. System Overview

RupeeRadar is an end-to-end personal finance assistant that accepts raw bank statement data, processes it through an AI-powered pipeline, and presents actionable spending insights via a clean dashboard.

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    ┌──────────────┐                     │
│  ─── User ───────▶│  Frontend    │◀────── Report ──────│
│                    │  (Dashboard) │       (PDF/HTML)    │
│                    └──────┬───────┘                     │
│                           │ HTTP/REST                   │
│                    ┌──────▼───────┐                     │
│                    │  Backend API │                     │
│                    │  (FastAPI)   │                     │
│                    └──────┬───────┘                     │
│                           │                             │
│          ┌────────────────┼────────────────┐            │
│          ▼                ▼                ▼            │
│   ┌────────────┐  ┌──────────────┐  ┌────────────┐    │
│   │  Parser    │  │  Classifier  │  │  Insights   │    │
│   │  (CSV/PDF) │  │  (AI/Rules)  │  │  Engine     │    │
│   └────────────┘  └──────────────┘  └────────────┘    │
│          │                │                │            │
│          └────────────────┼────────────────┘            │
│                           ▼                             │
│                    ┌──────────────┐                     │
│                    │  Storage     │                     │
│                    │  (In-Memory  │                     │
│                    │   or SQLite) │                     │
│                    └──────────────┘                     │
└─────────────────────────────────────────────────────────┘
```

---

## 2. Tech Stack Recommendations

| Layer              | Recommended             | Why                                                                 |
|--------------------|-------------------------|---------------------------------------------------------------------|
| **Frontend**       | React + TypeScript + Vite | Fast dev experience, rich ecosystem for charting & dashboards       |
| **Styling**        | Tailwind CSS            | Utility-first, rapid UI prototyping                                 |
| **Charts**         | Recharts or Chart.js    | Lightweight, declarative charting for spend breakdowns              |
| **Backend**        | Python (FastAPI)        | Excellent AI/ML library support, async, auto-generated OpenAPI docs |
| **Data Validation**| Pydantic v2             | Built into FastAPI, type-safe data models                           |
| **AI/ML**          | OpenAI API or local LLM | Transaction categorization + insight generation                      |
| **PDF Parsing**    | Camelot or Tabula-py    | Extract tabular data from PDF bank statements                       |
| **CSV Parsing**    | Pandas                  | Robust CSV/Excel parsing & cleaning                                 |
| **Storage**        | SQLite (via SQLAlchemy) | Zero-config, private, local-first — perfect for sensitive data      |
| **Deployment**     | Docker + local-first    | Easy setup, portable, privacy-preserving                            |

### Alternative Stack (Simpler)

If prioritising a faster prototype:
- **Frontend:** Single HTML page with vanilla JS + Chart.js CDN
- **Backend:** Python Flask with minimal dependencies
- **AI:** Local rule-based categorization + simple LLM prompt
- **Storage:** JSON file-based or in-memory

---

## 3. Component Architecture

### 3.1 Frontend (React + Vite + Tailwind)

```
src/
├── components/
│   ├── FileUploader.tsx         # Drag-and-drop bank statement upload
│   ├── TransactionTable.tsx     # Cleaned & categorized transaction list
│   ├── CategoryBreakdown.tsx    # Pie/bar chart of spend by category
│   ├── SpendSummary.tsx         # Cards: total income, spend, savings
│   ├── RecurringPayments.tsx    # List of detected recurring transactions
│   ├── InsightsPanel.tsx        # AI-generated personalized insights
│   ├── BiggestTransaction.tsx   # Highlight card for top transaction
│   └── ReportView.tsx           # Printable/downloadable report view
├── hooks/
│   ├── useUpload.ts             # File upload + progress tracking
│   └── useAnalysis.ts           # Fetch and cache analysis results
├── api/
│   └── client.ts                # Axios/fetch wrapper for backend API
├── types/
│   └── index.ts                 # TypeScript interfaces for all data models
├── App.tsx                      # Main app layout + routing
└── main.tsx                     # Entry point
```

### 3.2 Backend (Python FastAPI)

```
backend/
├── main.py                      # FastAPI app entry, CORS, routes
├── routers/
│   ├── upload.py                # POST /api/upload — accepts file
│   ├── analysis.py              # GET /api/analysis — fetch results
│   └── report.py                # GET /api/report — generate report
├── services/
│   ├── parser.py                # CSV/PDF parsing logic
│   ├── cleaner.py               # Transaction cleaning & normalization
│   ├── categorizer.py           # AI + rule-based categorization
│   ├── recurring_detector.py    # Pattern-based recurring detection
│   ├── metrics.py               # Financial metrics computation
│   └── insights.py              # AI-powered insight generation
├── models/
│   ├── transaction.py           # Pydantic models for transactions
│   ├── analysis.py              # Pydantic models for analysis results
│   └── report.py                # Pydantic models for report output
├── core/
│   ├── config.py                # App settings (API keys, categories, etc.)
│   └── categories.py            # Category definitions & keyword maps
├── utils/
│   ├── pdf_extractor.py         # PDF table extraction helpers
│   └── validators.py            # Input validation utilities
├── requirements.txt
└── Dockerfile
```

---

## 4. Data Flow

### Step-by-step Pipeline

```
[User Upload]
     │
     ▼
1. FILE INGESTION
   ├── Accept CSV / PDF / XLSX
   ├── Validate file format & size
   └── Extract raw text/rows
     │
     ▼
2. TRANSACTION PARSING
   ├── Detect column mappings (date, description, amount, etc.)
   ├── Parse dates to consistent format (YYYY-MM-DD)
   ├── Parse amounts to float (handle ₹, commas, negatives)
   └── Handle debit/credit distinction
     │
     ▼
3. CLEANING & NORMALIZATION
   ├── Strip whitespace & special characters
   ├── Normalize merchant names (e.g., "Swiggy*12345" → "Swiggy")
   ├── Remove duplicate transactions
   ├── Flag suspicious entries
   └── Output → List[StructuredTransaction]
     │
     ▼
4. CATEGORIZATION
   ├── AI-powered classification (LLM prompt)
   │   └── Fallback: keyword-based rule engine
   ├── Confidence scoring per category
   └── Output → List[CategorizedTransaction]
     │
     ▼
5. RECURRING DETECTION
   ├── Group by merchant name + amount (±tolerance)
   ├── Check for regular intervals (weekly, monthly, quarterly)
   ├── Flag subscriptions, EMIs, rent, SIPs, insurance
   └── Output → List[RecurringPayment]
     │
     ▼
6. METRICS COMPUTATION
   ├── Total income (sum of credits)
   ├── Total spend (sum of debits)
   ├── Savings = income − spend
   ├── Spend by category (amount + %)
   ├── Biggest transaction
   ├── Top 5 merchants by spend
   └── Output → FinancialMetrics
     │
     ▼
7. INSIGHT GENERATION
   ├── AI prompt with structured data → human-readable insights
   ├── "You spent ₹12,000 on food — 30% of your total spend"
   ├── "Your Netflix subscription costs ₹649/month"
   ├── "You saved ₹15,000 this month (20% of income)"
   └── Output → List[Insight]
     │
     ▼
8. DASHBOARD RENDERING
   └── Send all structured data to frontend
       └── User views charts, tables, insights, report
```

---

## 5. Data Models

### 5.1 Transaction (Cleaned)

```python
class Transaction(BaseModel):
    id: str                          # UUID
    date: date                       # Normalized date
    description: str                 # Cleaned description
    original_description: str        # Raw original text (for reference)
    amount: float                    # Always positive
    type: Literal["debit", "credit"] # Income or expense
    category: str                    # Food, Travel, Shopping, etc.
    category_confidence: float       # 0.0–1.0
    merchant: str | None             # Extracted merchant name
    is_recurring: bool               # Flagged by recurring detector
    recurring_type: str | None       # subscription, emi, rent, sip, insurance
    tags: list[str]                  # Additional tags
```

### 5.2 FinancialMetrics

```python
class FinancialMetrics(BaseModel):
    total_income: float
    total_spend: float
    savings: float
    savings_rate: float                         # %
    top_categories: list[CategorySpend]         # Sorted by amount desc
    top_merchants: list[MerchantSpend]          # Sorted by amount desc
    biggest_transaction: Transaction | None
    monthly_spend: float
    transaction_count: int
```

### 5.3 CategorySpend

```python
class CategorySpend(BaseModel):
    category: str
    amount: float
    percentage: float       # % of total spend
    transaction_count: int
```

### 5.4 RecurringPayment

```python
class RecurringPayment(BaseModel):
    merchant: str
    category: str
    amount: float
    frequency: str              # "monthly", "weekly", "quarterly"
    next_expected_date: date
    type: str                   # subscription, emi, rent, sip, insurance
    transactions: list[Transaction]
```

### 5.5 Insight

```python
class Insight(BaseModel):
    title: str                  # Short headline
    description: str            # Human-readable sentence
    type: str                   # "spending", "saving", "recurring", "alert"
    severity: str               # "info", "warning", "positive"
    amount: float | None        # Relevant amount if applicable
```

### 5.6 AnalysisResponse

```python
class AnalysisResponse(BaseModel):
    file_name: str
    parsed_at: datetime
    transactions: list[Transaction]
    total_transactions: int
    recurring_payments: list[RecurringPayment]
    metrics: FinancialMetrics
    insights: list[Insight]
```

---

## 6. API Design

### 6.1 Upload Bank Statement

```
POST /api/upload
Content-Type: multipart/form-data

Request:
  file: File (CSV, PDF, XLSX)

Response (202 Accepted):
{
  "job_id": "uuid",
  "status": "processing",
  "message": "File received. Analysis in progress."
}
```

### 6.2 Get Analysis Results

```
GET /api/analysis/{job_id}

Response (200 OK):
{
  "status": "completed",
  "data": AnalysisResponse   // See 5.6 above
}

Response (200 OK — still processing):
{
  "status": "processing",
  "data": null
}
```

### 6.3 Download Report

```
GET /api/report/{job_id}?format=pdf|html

Response (200 OK):
  Content-Type: application/pdf  or  text/html
  Body: Report file bytes
```

### 6.4 Health Check

```
GET /api/health

Response (200 OK):
{
  "status": "ok",
  "version": "1.0.0"
}
```

---

## 7. AI/ML Integration Strategy

### Categorization Approach

| Level | Method              | Details |
|-------|---------------------|---------|
| **Primary** | LLM-based (OpenAI GPT-4 mini or similar) | Single API call with batch of cleaned descriptions → categorized results |
| **Fallback** | Keyword + Regex rules | Merchant name → category mapping with configurable keywords |
| **Hybrid** | Both | Use LLM when confident (>0.9), else fallback to rules for re-check |

### Insight Generation Prompt Strategy

```
System: You are a personal finance analyst. Given the user's transaction data,
generate 3-5 concise, personalized insights. Use actual amounts and percentages.
Focus on: biggest spending categories, unusual spending, recurring costs,
savings opportunities, and positive habits.

User: [structured JSON of metrics + top transactions + recurring payments]

Assistant: [returns JSON array of Insight objects]
```

### Privacy Consideration for AI

- **Option A (Local):** Use a local LLM (Ollama + Llama 3 / Mistral) — data never leaves the machine.
- **Option B (Cloud):** Use OpenAI API — disclose clearly to the user, send minimal data (only cleaned descriptions, not raw statements).
- **Recommendation:** Implement a toggle in the UI — "Use local AI" vs. "Use cloud AI (faster)."

---

## 8. Recurring Transaction Detection Algorithm

```
For each transaction grouped by (merchant, amount_range):
  1. Sort by date ascending
  2. Calculate date differences between consecutive transactions
  3. If 3+ transactions with consistent intervals (±3 days):
     - Weekly: intervals of 7 ± 2 days
     - Monthly: intervals of 28-31 days
     - Quarterly: intervals of 85-95 days
  4. Check description for keywords: "subs", "emi", "rent", "sip", "insurance", "premium"
  5. Flag as recurring if: consistent intervals OR keyword match
```

---

## 9. Categorization Rules (Fallback Keyword Map)

```python
CATEGORY_KEYWORDS = {
    "Food":         ["swiggy", "zomato", "restaurant", "cafe", "dine", "food", "pizza", "burger"],
    "Travel":       ["uber", "ola", "metro", "cab", "flight", "irctc", "bus", "train", "taxi"],
    "Shopping":     ["amazon", "flipkart", "myntra", "meesho", "shopping", "mall", "store"],
    "Bills":        ["electricity", "water bill", "broadband", "phone bill", "recharge"],
    "EMI":          ["emi", "loan"],
    "Subscriptions":["netflix", "prime", "hotstar", "spotify", "youtube premium", "icloud"],
    "Salary":       ["salary", "credit salary", "payroll"],
    "Rent":         ["rent", "rental"],
    "Investments":  ["sip", "mutual fund", "stock", "nifty", "ppf", "nps"],
}
```

---

## 10. Dashboard Wireframe (Textual)

```
┌──────────────────────────────────────────────────┐
│  🏠 RupeeRadar                          [Upload] │
├──────────────────────────────────────────────────┤
│  ┌──────────────┐ ┌─────────────┐ ┌───────────┐│
│  │  Total Income │ │ Total Spend │ │  Savings  ││
│  │   ₹85,000     │ │  ₹62,000    │ │  ₹23,000  ││
│  └──────────────┘ └─────────────┘ └───────────┘│
├──────────────────────────────────────────────────┤
│  ┌──────────────┐       ┌────────────────────┐  │
│  │  Top Categories │     │  Recurring Payments│  │
│  │  ● Food   ₹18K  │     │  ● Netflix ₹649/🧊│  │
│  │  ● Rent   ₹15K  │     │  ● Rent    ₹15K/🧊│  │
│  │  ● Bills   ₹8K  │     │  ● SIP      ₹5K/🧊│  │
│  │  ● Travel  ₹6K  │     │  ──────────────── │  │
│  │  ● Shop    ₹5K  │     │  Total: 5 recurring│  │
│  └──────────────┘       └────────────────────┘  │
├──────────────────────────────────────────────────┤
│  📊 Spend Trend (Chart)                         │
│  ████████████████████████░░░░░░  │              │
├──────────────────────────────────────────────────┤
│  💡 AI Insights                                 │
│  • You spent ₹18K on food — 29% of total spend  │
│  • 5 recurring payments totalling ₹22K/month    │
│  • Your biggest expense is Rent at ₹15K         │
│  • You saved ₹23K — that's 27% of income ✓      │
├──────────────────────────────────────────────────┤
│  [📄 Download Full Report]                       │
└──────────────────────────────────────────────────┘
```

---

## 11. Deployment Strategy

### Local-First (Default)

| Component  | How to Run                              |
|------------|-----------------------------------------|
| Backend    | `uvicorn main:app --host 0.0.0.0:8000` |
| Frontend   | `npm run dev` → `localhost:5173`        |
| Database   | SQLite file (auto-created)              |
| AI         | Local via Ollama OR cloud API key       |

### Docker (Portable)

```
docker-compose up
├── frontend (nginx, port 80)
├── backend  (uvicorn, port 8000)
└── (optional) ollama for local AI
```

### CI/CD (Optional)

- GitHub Actions for linting + testing
- Docker image build on push to main

---

## 12. Privacy & Security Considerations

| Concern                  | Mitigation                                           |
|--------------------------|------------------------------------------------------|
| **Data Storage**         | SQLite by default — data stays on the user's machine |
| **AI Data Handling**     | Option for local LLM; cloud AI only sends descriptions, not raw data |
| **File Disposal**        | Auto-delete uploaded file after parsing completes    |
| **No External APIs**     | All computation can run offline (with local AI)      |
| **CORS**                 | Backend restricts to frontend origin                 |
| **No User Accounts**     | No authentication needed — completely anonymous      |

---

## 13. Development Phases

| Phase | Scope                                      | Est. Effort |
|-------|--------------------------------------------|-------------|
| **1** | Backend: CSV parsing + cleaning + basic metrics | 2 days      |
| **2** | Backend: AI categorization + recurring detection | 2 days      |
| **3** | Backend: Insight generation + report export     | 1 day       |
| **4** | Frontend: File upload + transaction table       | 1 day       |
| **5** | Frontend: Dashboard + charts + insights panel   | 2 days      |
| **6** | Integration testing + polish + deployment       | 1 day       |

**Total:** ~9 days for a complete prototype.

---

## 14. Key Design Decisions

1. **AI-categorization with rule fallback** — Ensures high accuracy while gracefully handling edge cases.
2. **Local-first architecture** — Sensitive financial data never leaves the user's machine unless explicitly opted in.
3. **Stateless API with job IDs** — Simple, no auth required, works for local-first usage.
4. **SQLite over PostgreSQL** — Zero config, no server process, perfect for a local-first prototype.
5. **React + Vite over Next.js** — Simpler, no SSR needed for a local dashboard app.
6. **Asynchronous processing pipeline** — Upload returns immediately, frontend polls for results.

---

*Generated from docs/context.md and docs/problemStatement.txt*
