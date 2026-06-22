# RupeeRadar — Implementation Plan

> **Project:** AI-Powered Personal Finance Assistant  
> **Source:** docs/problemStatement.txt, docs/architecture.md  
> **Status:** Planning Phase  
> **Version:** 2.0 (Aligned with Architecture)

---

## Overview

RupeeRadar is an end-to-end solution that converts raw financial transaction data into meaningful personal finance insights. The application allows users to upload bank statement data, extract and clean transactions, categorize expenses, detect recurring payments, generate spending insights, and present the results in a dashboard.

This document breaks the implementation into **6 phases**, each with clear deliverables, technical details, and acceptance criteria — fully aligned with the system architecture.

---

## Tech Stack

| Layer | Recommended | Rationale |
|-------|-------------|-----------|
| **Frontend** | React + TypeScript + Vite | Fast dev experience, rich ecosystem for charting & dashboards |
| **Styling** | Tailwind CSS | Utility-first, rapid UI prototyping |
| **Charts** | Recharts or Chart.js | Lightweight, declarative charting for spend breakdowns |
| **Backend** | Python (FastAPI) | Excellent AI/ML library support, async, auto-generated OpenAPI docs |
| **Data Validation** | Pydantic v2 | Built into FastAPI, type-safe data models |
| **AI/ML** | OpenAI API (GPT-4o-mini) or local LLM (Ollama) | Transaction categorization + insight generation |
| **PDF Parsing** | Camelot or Tabula-py | Extract tabular data from PDF bank statements |
| **CSV Parsing** | Pandas | Robust CSV/Excel parsing & cleaning |
| **Storage** | SQLite (via SQLAlchemy) | Zero-config, private, local-first — perfect for sensitive data |
| **Deployment** | Docker + local-first | Easy setup, portable, privacy-preserving |

---

## Phase 1: Backend Foundation — Parsing, Cleaning & Basic Metrics

**Goal:** Build the backend core: CSV/PDF parsing, transaction cleaning, data models, and financial metrics computation.

**Architecture Alignment:** `backend/` structure per architecture §3.2; data models per §5; data flow steps 1–3 & 6.

### Tasks

1. **Initialize Backend Project Structure**
   ```
   backend/
   ├── main.py                  # FastAPI app entry, CORS, routes
   ├── routers/
   │   ├── upload.py            # POST /api/upload — accepts file
   │   ├── analysis.py          # GET /api/analysis/{job_id}
   │   └── report.py            # GET /api/report/{job_id}
   ├── services/
   │   ├── parser.py            # CSV/PDF parsing logic
   │   ├── cleaner.py           # Transaction cleaning & normalization
   │   ├── metrics.py           # Financial metrics computation
   │   └── ... (added in later phases)
   ├── models/
   │   ├── transaction.py       # Pydantic models for transactions
   │   ├── analysis.py          # Pydantic models for analysis results
   │   └── report.py            # Pydantic models for report output
   ├── core/
   │   ├── config.py            # App settings (API keys, categories, etc.)
   │   └── categories.py        # Category definitions & keyword maps
   ├── utils/
   │   ├── pdf_extractor.py     # PDF table extraction helpers
   │   └── validators.py        # Input validation utilities
   ├── requirements.txt
   └── Dockerfile
   ```

2. **Define Data Models (Pydantic v2)**
   - `Transaction` (per architecture §5.1):
     - `id: str` (UUID)
     - `date: date` (normalized YYYY-MM-DD)
     - `description: str` (cleaned description)
     - `original_description: str` (raw original text for reference)
     - `amount: float` (always positive)
     - `type: Literal["debit", "credit"]`
     - `category: str` (Food, Travel, Shopping, Bills, EMI, Subscriptions, Salary, Rent, Investments, Other)
     - `category_confidence: float` (0.0–1.0)
     - `merchant: str | None` (extracted merchant name)
     - `is_recurring: bool`
     - `recurring_type: str | None` (subscription, emi, rent, sip, insurance)
     - `tags: list[str]`
   - `CategorySpend` (per architecture §5.3):
     - `category: str`, `amount: float`, `percentage: float`, `transaction_count: int`
   - `RecurringPayment` (per architecture §5.4):
     - `merchant: str`, `category: str`, `amount: float`, `frequency: str`, `next_expected_date: date`, `type: str`, `transactions: list[Transaction]`
   - `Insight` (per architecture §5.5):
     - `title: str`, `description: str`, `type: str` (spending/saving/recurring/alert), `severity: str` (info/warning/positive), `amount: float | None`
   - `FinancialMetrics` (per architecture §5.2):
     - `total_income: float`, `total_spend: float`, `savings: float`, `savings_rate: float`, `top_categories: list[CategorySpend]`, `top_merchants: list[MerchantSpend]`, `biggest_transaction: Transaction | None`, `monthly_spend: float`, `transaction_count: int`
   - `MerchantSpend`: `merchant: str`, `amount: float`, `category: str`, `transaction_count: int`
   - `AnalysisResponse` (per architecture §5.6):
     - `file_name: str`, `parsed_at: datetime`, `transactions: list[Transaction]`, `total_transactions: int`, `recurring_payments: list[RecurringPayment]`, `metrics: FinancialMetrics`, `insights: list[Insight]`

3. **Storage Layer**
   - SQLite via SQLAlchemy with async sessions
   - Alembic migrations for schema versioning
   - Repository pattern for CRUD operations
   - In-memory job store for async processing status

4. **CSV Parser** (`services/parser.py`)
   - Auto-detect column mappings (date, description, amount, balance, etc.)
   - Handle common Indian bank CSV formats (HDFC, ICICI, SBI, Axis)
   - Normalize date formats to YYYY-MM-DD
   - Parse amounts to float (handle ₹, commas, negatives)
   - Handle debit/credit distinction
   - Extract merchant name from description

5. **Cleaning & Normalization** (`services/cleaner.py`)
   - Strip whitespace & special characters
   - Normalize merchant names (e.g., "Swiggy*12345" → "Swiggy")
   - Remove duplicate transactions (by date + description + amount)
   - Flag suspicious entries (missing amounts, future dates)
   - Validate the "Golden Rule": Opening Balance + Sum(Credits) − Sum(Debits) ≈ Closing Balance
   - Output → `List[Transaction]`

6. **PDF Parser (Basic)** (`utils/pdf_extractor.py`)
   - Extract text using PyPDF2 / pymupdf
   - Use Camelot for table extraction from digitally-generated PDFs
   - Fallback to LLM-based extraction for complex layouts

7. **Metrics Computation** (`services/metrics.py`)
   - Implement `FinancialMetrics` calculation:
     - Total income (sum of credits)
     - Total spend (sum of debits)
     - Savings = income − spend
     - Savings rate (% of income)
     - Top 5 categories by spend (with % and transaction count)
     - Top 5 merchants by spend
     - Biggest single transaction (credit and debit)
     - Average daily spend
     - Number of transactions

8. **API: Upload Endpoint** (`routers/upload.py`)
   - `POST /api/upload` - accepts CSV or PDF files via `multipart/form-data`
   - File validation (size limit, format check)
   - Store file temporarily for processing
   - Return `202 Accepted` with `{ "job_id": "uuid", "status": "processing", "message": "File received. Analysis in progress." }`
   - Trigger async processing pipeline in background

9. **API: Analysis Polling Endpoint** (`routers/analysis.py`)
   - `GET /api/analysis/{job_id}`
   - If processing: `{ "status": "processing", "data": null }`
   - If completed: `{ "status": "completed", "data": AnalysisResponse }`

10. **Core Configuration** (`core/config.py`)
    - API key settings (OpenAI, etc.)
    - Category definitions
    - File upload limits
    - App version

11. **Create Seed/Test Data**
    - Generate synthetic bank statement CSV with 50+ realistic Indian transactions
    - Include edge cases: EMI deductions, UPI transfers, subscriptions, salary credit, rent

### Deliverables
- Runnable FastAPI app with upload + analysis polling endpoints
- Fully implemented CSV parser for 3+ Indian bank formats
- Transaction cleaning pipeline with deduplication and balance validation
- Financial metrics computation engine
- SQLite storage with Alembic migrations
- Synthetic test data CSV
- In-memory job queue for async processing

### Acceptance Criteria
- [ ] `uvicorn main:app` starts without errors
- [ ] `GET /api/health` returns `{"status": "ok", "version": "1.0.0"}`
- [ ] `POST /api/upload` with test CSV returns `202 Accepted` with a job_id
- [ ] `GET /api/analysis/{job_id}` returns `"status": "completed"` with `AnalysisResponse`
- [ ] Metrics are mathematically correct: income − spend = savings
- [ ] Top 5 categories match manual inspection of test data
- [ ] Balance validation passes (Golden Rule check)
- [ ] Alembic migrations run cleanly (`alembic upgrade head`)

---

## Phase 2: AI Categorization & Recurring Detection

**Goal:** Implement AI-powered transaction categorization with rule-based fallback, plus recurring payment detection.

**Architecture Alignment:** Data flow steps 4–5; services/categorizer.py + services/recurring_detector.py; AI/ML integration per §7; keyword map per §9; algorithm per §8.

### Tasks

1. **Categorization Service** (`services/categorizer.py`)
   - **Primary (LLM-based):**
     - Create async OpenAI client with retry logic, rate limiting, and token budgeting
     - Build prompt sending batches of 10-15 raw descriptions to GPT-4o-mini:
       ```
       System: You are a financial transaction categorizer. Given the following raw bank
       transaction descriptions, classify each into exactly one category:
       Food, Travel, Shopping, Bills, EMI, Subscriptions, Salary, Rent,
       Investments, or Other. Also extract the merchant name.

       Return JSON array: [{"original": "...", "cleaned": "...",
       "category": "...", "merchant": "...", "confidence": 0.95}]
       ```
     - Parse LLM response with Pydantic validation
     - Handle failed classifications with "Other" fallback at low confidence
     - Update transaction with category, category_confidence, merchant

   - **Fallback (Keyword + Regex Rules)** — per architecture §9:
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

   - **Hybrid approach:**
     - Use LLM when confidence > 0.9
     - Fallback to rules for re-check when confidence is lower (0.5–0.9)
     - Use rules exclusively when offline / no API key

2. **Recurring Payment Detector** (`services/recurring_detector.py`)
   - Algorithm per architecture §8:
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
   - Merchant name normalization for grouping (fuzzy matching)
   - Amount tolerance (±5% for same merchant)
   - Generate `RecurringPayment` objects with:
     - merchant, category, amount, frequency, next_expected_date, type, list of transactions
   - Built-in manual override: `PUT /api/analysis/{job_id}/transactions/{id}/recurring`

3. **Update Analysis Pipeline**
   - Wire categorizer + recurring detector into the async processing pipeline after parsing/cleaning
   - Store categorized transactions and recurring payments in the job result

4. **Configuration** (`core/categories.py`)
   - Category definitions and keyword maps as importable constants
   - Environment-based API key configuration (`OPENAI_API_KEY`)
   - AI provider toggle (openai / local / rules-only)
   - Confidence thresholds for hybrid mode

### Deliverables
- AI-powered categorization with >85% accuracy on test data
- Keyword-based fallback covering all 10 categories
- Recurring payment detection showing subscriptions, EMIs, rent, SIPs
- Manual override capability for misclassifications
- AI toggle (cloud/local/offline) configuration

### Acceptance Criteria
- [ ] 50 test transactions are categorized within 10 seconds (API mode)
- [ ] Recurring transactions (EMI, rent, Netflix, etc.) are correctly flagged
- [ ] Manual category override works and persists
- [ ] Rule-based fallback categorizes at least 60% of transactions when offline
- [ ] Category keyword map covers all 10 categories with 5+ keywords each
- [ ] Recurring detection correctly identifies monthly, weekly, quarterly patterns

---

## Phase 3: Insight Generation & Report Export

**Goal:** Generate personalized AI-driven insights and provide downloadable report functionality.

**Architecture Alignment:** Data flow step 7; services/insights.py; GET /api/report/{job_id}; Insight model per §5.5.

### Tasks

1. **Insight Generation Service** (`services/insights.py`)
   - Build LLM prompt with structured financial data:
     ```
     System: You are a personal finance analyst. Given the user's transaction data,
     generate 3-5 concise, personalized insights. Use actual amounts and percentages.
     Focus on: biggest spending categories, unusual spending, recurring costs,
     savings opportunities, and positive habits.
     Use Indian Rupee (₹) format for amounts.

     User data (JSON): {metrics + top_transactions + recurring_payments}

     Assistant: Return JSON array of Insight objects:
     [{"title": "...", "description": "...", "type": "spending|saving|recurring|alert",
       "severity": "info|warning|positive", "amount": 1234.56}]
     ```
   - Ensure insights reference actual transaction amounts per requirements
   - Aim for 3-5 insights per analysis
   - Classify each insight with type + severity for UI rendering

2. **Fallback Insight Generation (Offline)**
   - Rule-based template insights:
     - "Your biggest spending category is {category} at ₹{amount} — {percentage}% of total spend."
     - "You have {count} recurring payments totalling ₹{total}/month."
     - "You saved ₹{savings} this month — that's {rate}% of your income."
     - "Your biggest transaction was {description} at ₹{amount}."

3. **Report Generation** (`routers/report.py`)
   - `GET /api/report/{job_id}?format=pdf|html`
   - **HTML Report:** Jinja2 template rendering with embedded Chart.js visualization
   - **PDF Report:** Convert HTML to PDF using weasyprint or reportlab
   - Report includes (per architecture §10 dashboard wireframe):
     - Executive summary (income, spend, savings, savings rate)
     - Category breakdown with percentages
     - Top 5 transactions (credits and debits)
     - Recurring payments list with frequency
     - 3+ personalized insights with amounts
     - Full transaction log table
   - Download button available on frontend dashboard

4. **Update Analysis Pipeline**
   - Wire insight generator into the async pipeline after categorization
   - Include insights in the `AnalysisResponse` returned to frontend

### Deliverables
- AI-powered insight generation producing 3-5 personalized insights
- Rule-based fallback insights for offline mode
- Downloadable HTML report with embedded charts
- Downloadable PDF report
- All insights reference actual transaction amounts

### Acceptance Criteria
- [ ] At least 3 insights generated per analysis
- [ ] Insights reference specific transaction amounts
- [ ] Rule-based fallback generates coherent insights without AI
- [ ] HTML report renders correctly with all sections
- [ ] PDF report downloads and displays all required data
- [ ] Report includes category breakdown, top transactions, recurring list, and insights

---

## Phase 4: Frontend Foundation — Upload & Transaction Table

**Goal:** Build the React frontend foundation with file upload and transaction browsing.

**Architecture Alignment:** Frontend structure per §3.1; API integration per §6.

### Tasks

1. **Initialize Frontend Project Structure**
   ```
   src/
   ├── components/
   │   ├── FileUploader.tsx         # Drag-and-drop bank statement upload
   │   ├── TransactionTable.tsx     # Cleaned & categorized transaction list
   │   ├── CategoryBreakdown.tsx    # Pie/bar chart of spend by category (placeholder)
   │   ├── SpendSummary.tsx         # Cards: total income, spend, savings (placeholder)
   │   ├── RecurringPayments.tsx    # List of detected recurring transactions (placeholder)
   │   ├── InsightsPanel.tsx        # AI-generated personalized insights (placeholder)
   │   ├── BiggestTransaction.tsx   # Highlight card for top transaction (placeholder)
   │   └── ReportView.tsx           # Printable/downloadable report view (placeholder)
   ├── hooks/
   │   ├── useUpload.ts             # File upload + progress tracking + job polling
   │   └── useAnalysis.ts           # Fetch and cache analysis results by job_id
   ├── api/
   │   └── client.ts                # Axios/fetch wrapper for backend API
   ├── types/
   │   └── index.ts                 # TypeScript interfaces for all data models
   ├── App.tsx                      # Main app layout + routing
   └── main.tsx                     # Entry point
   ```

2. **Project Setup**
   - React + Vite + TypeScript + Tailwind CSS
   - React Router for navigation: `/upload`, `/dashboard`, `/transactions`, `/insights`
   - Shared layout with sidebar navigation
   - Axios for HTTP client

3. **TypeScript Data Models** (`types/index.ts`)
   - Define interfaces matching backend Pydantic models:
     - `Transaction`, `CategorySpend`, `RecurringPayment`, `Insight`
     - `FinancialMetrics`, `MerchantSpend`, `AnalysisResponse`
     - `UploadResponse`, `JobStatus`

4. **API Client** (`api/client.ts`)
   - `uploadFile(file: File): Promise<UploadResponse>` — POST /api/upload
   - `getAnalysis(jobId: string): Promise<AnalysisResponse>` — GET /api/analysis/{job_id}
   - `downloadReport(jobId: string, format: 'pdf' | 'html'): Promise<Blob>` — GET /api/report/{job_id}
   - Progress tracking for uploads

5. **Custom Hooks**
   - `useUpload()`:
     - Manages file selection, upload progress, job_id return
     - Auto-transitions to dashboard after upload completes
   - `useAnalysis(jobId: string)`:
     - Polls GET /api/analysis/{job_id} every 2 seconds while processing
     - Caches completed results
     - Returns loading/error/success states

6. **Upload Page (`/upload`)**
   - `FileUploader.tsx` component:
     - Drag-and-drop file upload zone with visual feedback
     - File picker for CSV/PDF selection (with format badge)
     - Upload progress indicator (progress bar %)
     - Processing status display (spinner → success/error/summary)
     - Auto-navigate to dashboard on success

7. **Transactions Page (`/transactions`)**
   - `TransactionTable.tsx` component:
     - Searchable by description/merchant/category
     - Sortable columns: Date, Description, Merchant, Amount, Category, Recurring
     - Filterable by category, type (credit/debit), recurring status
     - Inline category editing (dropdown) with auto-save
     - Bulk category re-assignment via multi-select
     - Pagination (50 per page) with page size selector

8. **Responsive Layout**
   - Sidebar navigation (collapses to hamburger on mobile)
   - Shared header with app title
   - Loading states (skeleton loaders)
   - Error states & empty states

### Deliverables
- Fully functional React app with routing and layout
- File upload page with drag-and-drop + progress tracking
- Transaction table with search, sort, filter, pagination, inline editing
- API client with job polling for async results
- All data models typed in TypeScript

### Acceptance Criteria
- [ ] File upload with drag-and-drop works and shows progress
- [ ] Upload returns job_id and auto-redirects to dashboard area
- [ ] Transaction table renders with correct data from API
- [ ] Search, sort, filter, and pagination all work
- [ ] Inline category editing saves to backend
- [ ] Mobile layout is usable
- [ ] No console errors

---

## Phase 5: Frontend Dashboard, Charts & Insights Panel

**Goal:** Build the main dashboard with visualizations, recurring payments view, and AI insights display.

**Architecture Alignment:** Wireframe per §10; all remaining components per §3.1.

### Tasks

1. **Dashboard Page (`/dashboard`)**
   - Layout per architecture §10 wireframe:
     ```
     ┌──────────────────────────────────────────────────┐
     │  Stats Cards Row                                 │
     │  ┌──────────────┐ ┌─────────────┐ ┌───────────┐ │
     │  │ Total Income │ │ Total Spend │ │  Savings  │ │
     │  │   ₹85,000    │ │   ₹62,000   │ │  ₹23,000  │ │
     │  └──────────────┘ └─────────────┘ └───────────┘ │
     ├──────────────────────────────────────────────────┤
     │  Two-Column Layout                               │
     │  ┌────────────────┐     ┌────────────────────┐   │
     │  │ Top Categories  │     │ Recurring Payments │   │
     │  │ (Chart + List)  │     │    (Card List)     │   │
     │  └────────────────┘     └────────────────────┘   │
     ├──────────────────────────────────────────────────┤
     │  Spend Trend Chart (Area/Bar chart)              │
     ├──────────────────────────────────────────────────┤
     │  AI Insights Panel                               │
     └──────────────────────────────────────────────────┘
     ```

2. **SpendSummary Component** (`SpendSummary.tsx`)
   - Summary cards: Total Income, Total Spend, Savings, Savings Rate
   - Each card: icon, label, amount in ₹, color-coded (green for income/savings, red for spend)
   - Animated number transitions
   - Skeleton loading state

3. **CategoryBreakdown Component** (`CategoryBreakdown.tsx`)
   - Donut/pie chart showing expense distribution by category (Recharts)
   - Clickable slices to filter transactions by category
   - Legend with color coding and percentages
   - Alternative: horizontal bar chart for top categories
   - Hover tooltips showing exact amounts

4. **BiggestTransaction Component** (`BiggestTransaction.tsx`)
   - Highlight card for largest debit and largest credit
   - Shows description, amount, date, merchant
   - Visual prominence with icon

5. **RecurringPayments Component** (`RecurringPayments.tsx`)
   - Card list of detected recurring transactions
   - Each card: merchant logo/icon, amount, frequency badge, next expected date
   - Type indicator: subscription (🔁), EMI (🏦), rent (🏠), SIP (📈), insurance (🛡️)
   - Summary: "X recurring payments totalling ₹Y/month"

6. **Spend Trend Chart**
   - Area/bar chart showing income vs spend over time
   - Month-over-month comparison
   - Interactive with hover tooltips

7. **InsightsPanel Component** (`InsightsPanel.tsx`)
   - Clean card layout showing each insight
   - Each card styled by type + severity:
     - spending/warning → orange left border
     - saving/positive → green left border
     - recurring/info → blue left border
     - alert/warning → red left border
   - Each card: icon, title, description with highlighted amounts (bold ₹)
   - "Generate Insights" button (calls `POST /api/analysis/{id}/insights`)
   - Last generated timestamp
   - Copy-to-clipboard for sharing

8. **ReportView Component** (`ReportView.tsx`)
   - Printable report view (print-friendly CSS)
   - "Download PDF" and "Download HTML" buttons
   - Preview modal before download

9. **Responsive Design & Polish**
   - Mobile-responsive layout
   - Dark/light mode toggle (persisted in localStorage)
   - Smooth transitions and micro-interactions
   - Hover tooltips on all charts
   - Framer Motion for page transitions (optional)

### Deliverables
- Full dashboard with summary cards, category chart, recurring payments, and trend chart
- AI insights panel with styled cards and copy functionality
- Download report buttons
- Responsive design with dark/light mode

### Acceptance Criteria
- [ ] Dashboard loads and displays correct data from API
- [ ] Pie/donut chart renders correctly with proper labels and legends
- [ ] Summary cards show correct totals with ₹ formatting
- [ ] Recurring payments list displays correctly with frequency badges
- [ ] Insights panel shows at least 3 styled insights
- [ ] Dark/light mode toggle works and persists
- [ ] Mobile layout is functional
- [ ] Report download buttons trigger correct API calls

---

## Phase 6: Integration Testing, Privacy & Deployment

**Goal:** Tie everything together, test end-to-end, implement privacy measures, and package for deployment.

**Architecture Alignment:** Privacy per §12; deployment per §11; key design decisions per §14.

### Tasks

1. **End-to-End Integration Testing**
   - Full pipeline test: Upload → Parse → Clean → Categorize → Detect Recurring → Calculate Metrics → Generate Insights → Display Dashboard
   - Test with synthetic data (50+ transactions)
   - Test with at least 1 real/anonymized bank statement
   - Measure end-to-end latency and optimize hot paths
   - Error scenarios: invalid files, empty files, partial data, network failures during AI calls

2. **Privacy & Security Implementation** (per architecture §12)
   - SQLite storage — data stays on user's machine by default
   - Auto-delete uploaded file after parsing completes
   - CORS configuration — backend restricts to frontend origin
   - No user accounts — completely anonymous usage
   - AI Data Handling:
     - Cloud mode: only cleaned descriptions sent to OpenAI, never raw statements
     - Local mode: Ollama integration for fully offline processing
     - UI toggle: "Use local AI" vs "Use cloud AI (faster)"
   - Clear privacy notice on first launch:
     - What data is processed locally
     - What data (if any) is sent to external APIs
     - Option to run completely offline
   - `.env` configuration for API keys — never exposed to frontend

3. **Frontend Polish & Error Handling**
   - Error boundaries in React (per-component crash recovery)
   - Structured error responses from backend displayed as toast notifications
   - Offline detection — show banner when AI features unavailable
   - Rate limiting on AI endpoints (to control API costs)
   - Transaction export as CSV (download from transactions page)
   - User onboarding flow (first-time upload guide with tooltips)

4. **Deployment Strategy** (per architecture §11)

   **Option A: Docker Compose**
   ```
   docker-compose up
   ├── frontend (nginx, port 80)
   ├── backend  (uvicorn, port 8000)
   └── (optional) ollama for local AI
   ```

   **Option B: Local-First (Default)**
   - README with step-by-step setup:
     ```
     Backend: uvicorn main:app --host 0.0.0.0:8000
     Frontend: npm run dev → localhost:5173
     Database: SQLite file (auto-created)
     AI: Local via Ollama OR cloud API key
     ```

   **Option C: Standalone Launcher**
   - `run.sh` / `run.bat` script:
     - Python virtual environment setup
     - `pip install -r requirements.txt`
     - `npm install && npm run build`
     - `uvicorn backend.main:app`

5. **Docker Setup**
   - `Dockerfile` for backend (Python + Uvicorn)
   - `Dockerfile` for frontend (Node build + Nginx serve)
   - `docker-compose.yml` with:
     - Backend service (port 8000)
     - Frontend service (port 80)
     - Volume for SQLite persistence
     - Environment variables for API keys

6. **Documentation**
   - `README.md` with:
     - Project overview and screenshots
     - Tech stack summary
     - Quick start (local + Docker)
     - API documentation reference
     - Privacy disclosure
     - Configuration guide (AI toggle, API keys)

7. **CI/CD (Optional)**
   - GitHub Actions for linting + testing
   - Docker image build on push to main

### Deliverables
- Fully integrated, runnable application
- Docker Compose setup for one-command deployment
- Standalone launcher scripts
- Privacy notice and data handling disclosure
- AI toggle (local/cloud/offline)
- Comprehensive README with screenshots
- Error boundaries and offline detection

### Acceptance Criteria
- [ ] `docker-compose up` starts both frontend and backend
- [ ] End-to-end flow completes without errors on test data
- [ ] PDF report downloads with all required sections
- [ ] No data leakage — API key is not exposed client-side
- [ ] Application runs fully offline (with rule-based fallback) if no API key is configured
- [ ] Privacy notice is displayed on first launch
- [ ] CORS is properly configured
- [ ] Uploaded files are deleted after processing
- [ ] README covers setup, usage, and architecture at a glance

---

## Effort Estimation

| Phase | Description | Estimated Effort |
|-------|-------------|-----------------|
| 1 | Backend Foundation — Parsing, Cleaning & Basic Metrics | 2-3 days |
| 2 | AI Categorization & Recurring Detection | 2-3 days |
| 3 | Insight Generation & Report Export | 1-2 days |
| 4 | Frontend Foundation — Upload & Transaction Table | 2 days |
| 5 | Frontend Dashboard, Charts & Insights Panel | 2-3 days |
| 6 | Integration Testing, Privacy & Deployment | 1-2 days |
| **Total** | | **10-15 days** |

---

## Key Dependencies Graph

```
Phase 1 (Backend Foundation: Parse, Clean, Metrics)
    │
    ├────────────────────────────────────┐
    ▼                                     │
Phase 2 (AI Categorization + Recurring)   │
    │                                     │
    ▼                                     │
Phase 3 (Insights + Report Export)        │
    │                                     │
    └──────────┬──────────────────────────┘
               │
               ▼
       Phase 4 (Frontend: Upload + Table)
               │
               ▼
       Phase 5 (Frontend: Dashboard + Charts)
               │
               ▼
       Phase 6 (Integration + Privacy + Deploy)
```

---

## Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| LLM categorization accuracy too low | High | Rule-based fallback (§9 keyword map); hybrid approach with confidence threshold; manual inline override |
| PDF parsing fails on complex formats | Medium | Graceful fallback to LLM-based text extraction; Camelot for table extraction; clear user feedback |
| OpenAI API costs exceed budget | Medium | Batch processing in GPT-4o-mini (cheapest model); rate limiting; offline rule-based fallback |
| Real bank statements vary wildly in format | High | Phase 1 handles top 3 Indian bank formats; LLM-based extraction as universal fallback |
| Frontend performance with large datasets | Medium | Virtualized table (React Window); pagination at 50/page; lazy chart rendering |
| Async job processing complexity | Low | Simple in-memory job store for prototype; polling approach is well-understood pattern |
| Privacy concerns with financial data | Medium | Local-first SQLite; AI toggle (local/cloud/offline); clear privacy disclosure; auto-delete uploaded files |

---

## Architecture Alignment Summary

| Architecture § | Implementation Plan § | Status |
|----------------|----------------------|--------|
| §3.1 Frontend Structure | Phase 4, Phase 5 | ✅ Aligned |
| §3.2 Backend Structure | Phase 1 (initial), Phase 2-3 (extensions) | ✅ Aligned |
| §4 Data Flow (8 steps) | Phases 1-3 (steps 1-7), Phase 5 (step 8) | ✅ Aligned |
| §5 Data Models | Phase 1 (models), Phase 4 (TypeScript types) | ✅ Aligned |
| §6 API Design | Phase 1 (upload + analysis), Phase 3 (report) | ✅ Aligned |
| §7 AI/ML Integration | Phase 2 (categorization), Phase 3 (insights) | ✅ Aligned |
| §8 Recurring Detection Algorithm | Phase 2 | ✅ Aligned |
| §9 Category Keyword Map | Phase 2 (core/categories.py) | ✅ Aligned |
| §10 Dashboard Wireframe | Phase 5 | ✅ Aligned |
| §11 Deployment Strategy | Phase 6 | ✅ Aligned |
| §12 Privacy & Security | Phase 6 | ✅ Aligned |
| §14 Key Design Decisions | All phases | ✅ Aligned |

---

*Last updated: June 2026*
*Version: 2.0*
