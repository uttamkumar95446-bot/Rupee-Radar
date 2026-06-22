# RupeeRadar 💰

**AI-powered personal finance assistant** that transforms raw bank transaction data into meaningful financial insights. Upload your bank statement CSV or PDF and get instant categorization, spending analysis, recurring payment detection, and personalized AI-driven financial advice.

---

## ✨ Features

- **📄 Multi-Format Upload** — Supports CSV files from HDFC, ICICI, SBI, Axis, and other Indian banks, plus PDF bank statements.
- **🤖 AI-Powered Categorization** — Uses Groq/OpenAI LLMs to automatically categorize transactions with confidence scoring.
- **📊 Financial Dashboard** — Visual overview of income, spending, savings rate, top categories, and merchants.
- **🔁 Recurring Payment Detection** — Automatically identifies subscriptions, EMIs, rent, and other recurring transactions.
- **💡 AI Insights** — Personalized financial advice and anomalies detection.
- **🔍 Transaction Explorer** — Search, filter, sort, and manually override categories or recurring flags.
- **📈 Spending Trends** — Interactive charts showing spending patterns over time.
- **📋 Report Generation** — Downloadable HTML/PDF reports with charts and full transaction logs.
- **🌙 Dark Mode** — Built-in theme toggle with system preference detection.
- **🔒 Privacy-First** — Local processing by default; AI features are optional and configurable.

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+** — [Download](https://www.python.org/downloads/)
- **Node.js 18+** — [Download](https://nodejs.org/)
- **npm** (included with Node.js)

### One-Click Launcher

**Windows:**
```bash
run.bat
```

**macOS / Linux:**
```bash
bash run.sh
```

### Manual Setup

#### 1. Backend Setup

```bash
# Navigate to backend
cd backend

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys (optional — free tier works without keys)
```

#### 2. Frontend Setup

```bash
cd frontend
npm install
```

#### 3. Start Development Servers

**Terminal 1 — Backend:**
```bash
cd backend
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 — Frontend:**
```bash
cd frontend
npm run dev
```

#### 4. Open in Browser

Navigate to **[http://localhost:5173](http://localhost:5173)** and upload a bank statement to get started.

---

## 🔧 Configuration

### AI Provider

RupeeRadar supports three AI processing modes, configurable in the Settings panel:

| Mode | Description | API Key Required |
|------|-------------|:---:|
| **Local** | Lightweight processing on your device | ❌ |
| **Cloud** | Uses Groq/OpenAI for richer analysis | ✅ |
| **Offline** | Rule-based categorization only, fully private | ❌ |

Set your API keys in `backend/.env`:

```ini
LLM_PROVIDER=groq
GROQ_API_KEY=gsk_your_key_here  # Get at https://console.groq.com/keys
```

### Environment Variables

See [backend/.env.example](backend/.env.example) for a full list of configuration options.

---

## 🐳 Docker Deployment

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

### Run with Docker Compose

```bash
# Start both services
docker compose up -d

# The app will be available at http://localhost:80
```

### Build & Run Individually

```bash
# Backend
docker build -t rupeeradar-backend -f Dockerfile.backend .
docker run -d -p 8000:8000 --name rupeeradar-backend rupeeradar-backend

# Frontend
docker build -t rupeeradar-frontend -f Dockerfile.frontend .
docker run -d -p 80:80 --name rupeeradar-frontend rupeeradar-frontend
```

---

## 📁 Project Structure

```
rupeeradar/
├── backend/                 # FastAPI Python backend
│   ├── alembic/            # Database migrations
│   ├── core/               # Config, database, categories
│   ├── models/             # SQLAlchemy & Pydantic models
│   ├── routers/            # API endpoints (upload, analysis, report)
│   ├── seed_data/          # Sample bank statements for testing
│   ├── services/           # Business logic (parser, categorizer, insights, etc.)
│   ├── templates/          # Jinja2 HTML report templates
│   └── utils/              # PDF extraction, validators
├── frontend/               # React + TypeScript frontend
│   └── src/
│       ├── api/            # API client (axios)
│       ├── components/     # UI components
│       ├── hooks/          # Custom React hooks
│       ├── pages/          # Page-level components
│       ├── types/          # TypeScript type definitions
│       └── utils/          # Formatting utilities
├── Dockerfile.backend      # Backend Docker image
├── Dockerfile.frontend     # Frontend Docker image (nginx)
├── docker-compose.yml      # Multi-service orchestration
├── run.bat                 # Windows launcher
└── run.sh                  # Unix launcher
```

---

## 🧪 Testing

### Integration Test

Run the full pipeline test (health check → upload → analysis → overrides):

```bash
cd backend
python test_pipeline.py
```

### Manual Testing

1. Upload `backend/seed_data/sample_transactions.csv` via the web UI
2. Navigate to the Dashboard to view analysis results
3. Browse and filter transactions on the Transactions page
4. Try overriding a category or recurring flag
5. Download an HTML or PDF report
6. Toggle dark mode and AI mode in Settings

---

## 🛠 Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 19, TypeScript 6, Vite 8, Tailwind CSS 4 |
| **Backend** | Python 3.12+, FastAPI, SQLAlchemy (async) |
| **Database** | SQLite (dev), PostgreSQL (production-ready) |
| **AI/LLM** | Groq (Llama 3), OpenAI (GPT-4o-mini), local fallback |
| **Charts** | Recharts, Chart.js (reports) |
| **Deployment** | Docker, Docker Compose, nginx |

---

## 📄 API Documentation

Once the backend is running, interactive API docs are available at:

- **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)

### Key Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Health check |
| `POST` | `/api/upload` | Upload bank statement (CSV/PDF) |
| `GET` | `/api/analysis/{job_id}` | Poll analysis results |
| `GET` | `/api/report/{job_id}` | Download report (HTML/PDF) |
| `PUT` | `/api/analysis/{job_id}/transactions/{id}/category` | Override category |
| `PUT` | `/api/analysis/{job_id}/transactions/{id}/recurring` | Override recurring flag |

---

## 🤝 Contributing

Contributions are welcome! Feel free to open issues or submit pull requests.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the MIT License.

---

## 🙏 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/) and [React](https://react.dev/)
- AI powered by [Groq](https://groq.com/) and [OpenAI](https://openai.com/)
- Charts by [Recharts](https://recharts.org/) and [Chart.js](https://www.chartjs.org/)
