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

## Production hardening (rate limits & resilience)

### Rate limiting

AI-costly endpoints use a **sliding-window** limiter keyed by `user_id` (IP fallback):

| Endpoint | Default | Env var |
|----------|---------|---------|
| `POST /itineraries/generate` (Groq) | 5 / hour | `MAX_ITINERARY_REQUESTS_PER_HOUR` |
| `POST /landmarks/recognize` (Gemini) | 10 / hour | `MAX_SCAN_REQUESTS_PER_HOUR` |
| `POST /recommendations/generate` (local ML) | 30 / hour | `MAX_RECOMMENDATION_REQUESTS_PER_HOUR` |

**Why sliding window?** It matches “N requests per hour” for cost control and avoids the fixed-window burst at hour boundaries. Over limit → HTTP **429** with `retry_after` and a `Retry-After` header; rejections are logged (`event=rate_limit_rejected`).

Default backend is **in-memory** (fine for one uvicorn worker). For multiple workers/instances, set `REDIS_URL` — the same call sites automatically use a Redis sorted-set window (`pip install redis` is already listed in requirements).

### Circuit breaker

If Groq or Gemini errors spike (`CIRCUIT_BREAKER_FAILURE_THRESHOLD` within `CIRCUIT_BREAKER_WINDOW_SECONDS`), that provider’s circuit **opens** for `CIRCUIT_BREAKER_OPEN_SECONDS` and returns **503** with a maintenance-style message instead of burning more budget. `/health` exposes circuit status.

### Timeouts, retries, validation

- Configurable timeouts: Groq **15s** (chat JSON is usually fast), Gemini **20s** (vision + image upload needs more headroom).
- **Exponential backoff** retries (`AI_MAX_RETRIES`, default 2) only for transient failures (timeouts, network, 429/5xx) — not for 4xx/invalid input.
- Responses are validated (shape + JSON parse) before use; malformed payloads become controlled 502s, not crashes.

### Graceful degradation

- **Itinerary / scanner:** friendly UI copy + retry — never an endless spinner.
- **Recommendations:** if sklearn inference fails, fall back to popular destinations from `destinations.csv` so the page is never empty.
- **Logging:** stdlib logging with optional JSON (`LOG_JSON=true`) and structured fields (`event`, `endpoint`, `user_id`, `error_type`, `recovered`). We kept stdlib instead of adding Winston/Pino-style deps — it is already wired and ships cleanly to any log agent.
- **Sentry (optional):** set `SENTRY_DSN` to enable free-tier error tracking (`sentry-sdk[fastapi]`).

### Image uploads (albums + scanner)

Storage is **local disk** under `UPLOAD_DIRECTORY` (default `uploads/`).

| Limit | Default | Env |
|-------|---------|-----|
| Max size per photo | 10MB | `MAX_PHOTO_SIZE_MB` |
| Max photos per album | 50 | `MAX_PHOTOS_PER_ALBUM` |
| Max storage per user | 500MB | `MAX_STORAGE_PER_USER_MB` |
| Max files per request | 10 | `MAX_UPLOAD_BATCH_SIZE` |

**Validation:** client checks size/type for fast feedback; server re-reads with a byte cap, sniffs **magic bytes** (JPEG/PNG/WebP), then decodes with Pillow. Extension/`Content-Type` alone is never trusted.

**Compression (Pillow):** longest edge capped at `IMAGE_MAX_DIMENSION` (default **1920px**), re-encoded as **JPEG quality 85**, EXIF stripped after orientation fix.

Why these settings?
- 1920px is enough for gallery cards, PDF keepsakes, and Gemini (providers downsample further); raw 12MP camera shots waste disk and bandwidth.
- JPEG 85 is visually near-lossless for travel photos and stays compatible with ReportLab PDF export (WebP would need extra PDF handling).
- Typical phone photos shrink 5–10×, which cuts storage cost and speeds gallery loads.

The landmark scanner offers **Take Photo** (`capture="environment"`) and **Upload Photo**; camera-captured images go through the same compress/validate path. If the camera is blocked, the UI falls back to upload.

## Future improvements

- Mobile app / PWA for on-the-road scanning and album uploads
- Shared albums and public trip pages
- Offline map pins for itinerary stops and scanned landmarks
- Budget tracking from recommendations and itineraries
- Stronger recommendation feedback loop (likes, skips, trip outcomes)
- Multi-language landmark guides and itineraries
