# StoryMiles

AI travel companion that recommends destinations, builds day-by-day itineraries, identifies landmarks from photos, and turns trip pictures into downloadable albums.

Stack: React (TanStack Start), FastAPI, PostgreSQL, scikit-learn, Groq, Gemini.

## Features

- **Verified accounts** — register with any valid email, confirm a 6-digit email code, then sign in
- **Personalized recommendations** — ML model scores destinations from interests, budget, trip length, and travel style
- **Trip planner** — save preferences and generate a multi-day itinerary with Groq
- **Landmark scanner** — upload a photo; Gemini vision returns name, history, architecture notes, and visitor tips
- **Trip albums** — create albums, upload trip photos, browse a gallery, download a PDF keepsake
- **Dashboard** — overview of matches, saved preferences, and quick links into each tool

## Requirements

- Python 3.13
- PostgreSQL
- Node.js 20+
- Groq API key (itineraries)
- Gemini API key (landmark scanner)
- SMTP account or Gmail App Password (verification emails)

## Setup

Copy env templates and add your keys locally (never commit `.env`):

```powershell
copy backend\.env.example backend\.env
copy frontend\.env.example frontend\.env
```

Then:

```powershell
cd backend
.\scripts\setup_local.ps1
```

For Gmail delivery, enable 2-Step Verification on the sender account, create a
Google App Password, and set `SMTP_USERNAME`, `SMTP_PASSWORD`, and
`SMTP_FROM_EMAIL` in `backend/.env`. Do not use your normal Gmail password.

## Run

Backend:

```powershell
cd backend
.\scripts\run_dev.ps1
```

Frontend:

```powershell
cd frontend
npm install
npm run dev
```

Open http://localhost:8080 · API docs http://localhost:8000/docs

## Future improvements

- Mobile app / PWA for on-the-road scanning and album uploads
- Shared albums and public trip pages
- Offline map pins for itinerary stops and scanned landmarks
- Budget tracking and booking deep-links from recommendations
- Stronger recommendation feedback loop (likes, skips, trip outcomes)
- Multi-language landmark guides and itineraries
