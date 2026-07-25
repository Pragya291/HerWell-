# HerWellness Hub 🌸

A holistic health & wellness platform designed for women, covering menstrual & reproductive cycle tracking, mental wellness support with an AI companion, cycle-synced fitness guidance, and an evidence-based health library.

Built for hackathons — easy to run, local-first, zero mandatory external dependencies (includes smart fallback AI chatbot).

---

## 🌟 Key Features

1. **Menstrual & Reproductive Tracker**:
   - Monthly interactive calendar with period, fertile window, and ovulation indicators.
   - Dynamic cycle prediction algorithm (calculates cycle length, next period date, ovulation day, and current cycle phase).
   - Detailed daily logging: flow intensity, multi-select physical symptoms (cramps, bloating, fatigue, etc.), and personal notes.
   - Cycle history log.

2. **Mental Wellness & Vera AI Companion**:
   - Daily mood logging with emoji scale (1-5) and CBT-guided reflection journaling.
   - 30-day interactive mood trend line chart and 4-week mood aggregation.
   - **Vera AI Chatbot**: Empathetic wellness companion proxying OpenAI (`gpt-3.5-turbo`) with a rule-based fallback engine (no API key required!).
   - Crisis helpline resources and quick emergency access modal.

3. **Cycle-Synced Fitness Guidance**:
   - Tailored workout recommendations automatically updated based on your current cycle phase (Menstrual, Follicular, Ovulatory, Luteal).
   - Interactive workout logger with duration and intensity tracking.
   - Weekly activity metrics (total workout days & active minutes).

4. **Evidence-Based Health Library**:
   - 12 medical guides covering PCOS, Endometriosis, Menopause, Contraception, Mental Health, and Nutrition.
   - Real-time search filter and category pill navigation.
   - 3D interactive Myth-Buster flip cards.

5. **Authentication & Hackathon Demo Mode**:
   - Secure JWT token authentication with bcrypt password hashing.
   - **Instant Demo Mode**: One-click reviewer access without registration.

---

## 🛠 Tech Stack

- **Backend**: Python 3.8+ with **FastAPI**, **SQLAlchemy**, **Pydantic**, **python-jose** (JWT), **passlib** (bcrypt).
- **Database**: **SQLite** (`herwellness.db`).
- **Frontend**: Plain **HTML5**, **CSS3** (custom glassmorphism design system), **Vanilla JavaScript** (ES6+, Fetch API, Canvas charts, SPA architecture).
- **AI Chatbot**: **OpenAI API** (`gpt-3.5-turbo`) with intelligent fallback rule engine.

---

## 📁 Repository Structure

```
HerWell/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py          # FastAPI app entry point & static file server
│   │   ├── database.py      # SQLAlchemy SQLite configuration
│   │   ├── models.py        # Database ORM models (User, CycleLog, MoodLog, FitnessLog)
│   │   ├── schemas.py       # Pydantic data validation schemas
│   │   ├── auth.py          # JWT authentication & password hashing
│   │   ├── utils.py         # Cycle algorithm, seed data, Vera fallback engine
│   │   └── routers/
│   │       ├── auth.py      # Auth endpoints (/api/auth)
│   │       ├── cycles.py    # Period tracker endpoints (/api/cycle)
│   │       ├── mood.py      # Mental wellness endpoints (/api/mood)
│   │       ├── fitness.py   # Fitness endpoints (/api/fitness)
│   │       ├── health.py    # Health library endpoints (/api/health)
│   │       └── chat.py      # Vera chatbot proxy endpoint (/api/wellness/chat)
│   ├── static/
│   │   ├── index.html       # Single Page Application HTML
│   │   ├── css/style.css    # Responsive styles & design system
│   │   └── js/app.js        # Frontend SPA controller & fetch API client
│   ├── requirements.txt     # Python dependencies
│   └── .env.example         # Environment template
├── README.md
└── .gitignore
```

---

## 🚀 Quick Setup & Run Instructions

### 1. Prerequisites
- Python 3.8 or higher installed on your machine.

### 2. Create Virtual Environment & Install Dependencies
Open a terminal in the `backend/` directory:

```bash
# Navigate to backend directory
cd backend

# Create virtual environment (if not already created)
python -m venv venv

# Activate virtual environment
# On Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# On macOS / Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Configuration (Optional)
Copy `.env.example` to `.env` inside `backend/`:

```bash
cp .env.example .env
```
*(If `OPENAI_API_KEY` is not provided, Vera will automatically use the built-in empathetic fallback system).*

### 4. Run the Server
Launch the FastAPI app using Uvicorn:

```bash
uvicorn app.main:app --reload --port 8000
```

### 5. Access the Web Application
Open your web browser and navigate to:
```
http://localhost:8000
```

---

## 🎯 Demoing the App

1. **Instant Access**: On the login screen, click **"✨ Instant Demo Mode (No Login Required)"** to jump straight into the Dashboard with pre-loaded user state.
2. **Account Creation**: Alternatively, switch to the **Sign Up** tab to create a fresh user account with email and password.
3. **Period Tracker**: Navigate to **Tracker**, click on today's date in the calendar, log period flow / symptoms, and observe how predictions update dynamically.
4. **Vera Chatbot**: Go to **Wellness**, type a question or click a quick prompt like *"Can you guide me through a 4-7-8 breathing exercise?"*.
5. **Myth Buster Cards**: Go to **Library** and click any of the Myth Buster cards to test the 3D flip animation.
