# ResumePulse — AI-Powered ATS Resume Optimizer

A Chrome Extension that detects job postings while you browse, warns about visa restrictions and experience gaps, and uses Groq AI (Llama 3.3 70B) to generate tailored ATS-optimized resumes in seconds.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🔍 **Job Detection** | Automatically detects job postings on any website |
| 🛂 **Visa Warning** | Flags jobs requiring US citizenship or security clearance |
| ⚡ **Experience Gap Alert** | Warns when a job requires more experience than your profile |
| 🤖 **AI Resume Tailoring** | Groq AI rewrites your resume to match each job description |
| 📊 **ATS Score** | Scores your tailored resume before you apply (0-100) |
| 📄 **PDF Export** | Downloads a professionally formatted resume PDF |
| 📊 **Dashboard** | View all generated resumes with ATS scores and history |

---

## 🏗️ Tech Stack

| Layer | Technology |
|---|---|
| Chrome Extension | Manifest V3, Vanilla JS, CSS |
| Backend | Python, FastAPI, Uvicorn |
| Database | SQLite, SQLAlchemy ORM |
| AI | Groq API (Llama 3.3 70B) |
| NLP Scoring | Custom keyword extraction algorithm |
| PDF Generation | ReportLab |
| Auth | JWT tokens, bcrypt password hashing |

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- Google Chrome
- Groq API key (free at console.groq.com)
- Node.js (for live-server)

### Installation

**1. Clone the repo**
```bash
git clone https://github.com/YOUR_USERNAME/resumepulse.git
cd resumepulse
```

**2. Set up Python backend**
```bash
cd backend
py -3.10 -m venv venv
.\venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

**3. Configure environment**
```bash
cp .env.example .env
# Open .env and add your Groq API key
```

**4. Start the backend**
```bash
python -m uvicorn main:app --reload --port 8000
```

**5. Start the frontend**
```bash
# In a new terminal from project root
npm install -g live-server
live-server --port=5500
```

**6. Load the Chrome Extension**
1. Open Chrome → go to `chrome://extensions`
2. Enable **Developer mode**
3. Click **Load unpacked**
4. Select the `extension/` folder

**7. Create your account**
- Visit `http://127.0.0.1:5500/frontend/register.html`
- Create an account and paste your base resume

---

## 📁 Project Structure