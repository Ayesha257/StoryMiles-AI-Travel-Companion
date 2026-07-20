# StoryMiles — Project Specification

## Overview

StoryMiles is an AI-powered travel recommendation platform. The backend is a REST API that combines a trained ML recommender (Kaggle worldwide travel cities dataset) with LLM-powered itinerary generation and landmark recognition.

## Technology Stack

| Component | Requirement |
|---|---|
| API | FastAPI + Uvicorn |
| Database | PostgreSQL |
| ORM | SQLAlchemy Async + Alembic migrations |
| Auth | JWT (access + refresh), bcrypt password hashing |
| Validation | Pydantic v2 |
| AI | OpenAI / Groq for itineraries and landmark vision |
| ML | scikit-learn RandomForest trained on Kaggle-derived destinations |
| Deployment | Docker Compose (API + PostgreSQL) |

## ML Pipeline (`backend/ml-artifacts/`)

1. `01_load_real_destinations.py` — Kaggle CSV → `destinations.csv`
2. `02_generate_training_data.py` — synthetic training pairs → `training_pairs.csv`
3. `03_train_model.py` — train model → `recommender_model.pkl`, `feature_columns.pkl`
4. Runtime inference via `backend/app/ml/` loaded at startup

## Functional Requirements

### Authentication
- Register with email/password (optional name fields)
- Register response must include user + access_token + refresh_token
- Login returns access_token + refresh_token
- Refresh token endpoint
- Protected routes require valid JWT

### User Management
- GET `/api/v1/users/me` — authenticated user profile
- PATCH `/api/v1/users/me/profile` — update profile

### Preferences
- GET/PATCH `/api/v1/preferences/me` — travel styles, budget, trip days, etc.

### ML Recommendations
- POST `/api/v1/recommendations/generate` — rank destinations using trained model
- GET `/api/v1/recommendations/history` — past recommendation runs
- Model uses `ml-artifacts/destinations.csv` catalog (~559 cities)
- User travel styles/interests normalized to destination tag vocabulary

### User Destinations
- CRUD `/api/v1/destinations` — user-owned saved destinations (separate from ML catalog)

### Itineraries
- POST `/api/v1/itineraries/generate` — AI-generated day-by-day itinerary
- CRUD `/api/v1/itineraries` — save and manage itineraries

### Images & Landmarks
- POST `/api/v1/images` — upload with type/size validation
- POST `/api/v1/landmarks/recognize` — upload image, return landmark identification via Gemini vision
- Landmark response exposes structured fields (name, location, confidence, description, historical background, visitor tips)
- Landmark recognition uses `GEMINI_API_KEY` / `GEMINI_MODEL` (itineraries continue to use Groq)

### Trip Photo Albums
- Authenticated users can create albums with a title, destination, trip dates, and description
- Users can upload multiple JPG, PNG, or WebP trip photos to an album
- Album photos are stored through the existing validated image-upload pipeline
- GET `/api/v1/albums` — list the current user's albums
- POST `/api/v1/albums` — create an album
- GET `/api/v1/albums/{album_id}` — view an album and its ordered photos
- POST `/api/v1/albums/{album_id}/photos` — upload one or more photos
- DELETE `/api/v1/albums/{album_id}` — delete an album
- GET `/api/v1/albums/{album_id}/pdf` — generate and download a printable PDF keepsake
- Frontend `/albums` page supports album creation, multi-photo upload, gallery previews, and PDF download

### Health & Ops
- GET `/health` — API and ML model readiness
- Request logging and request ID middleware
- Graceful 503 when database unavailable

## API Compatibility Aliases (legacy contract paths)

| Legacy path | Canonical path |
|---|---|
| POST `/api/v1/preferences` | PATCH `/api/v1/preferences/me` |
| GET `/api/v1/recommendations` | GET `/api/v1/recommendations/history` |
| POST `/api/v1/landmark/identify` | POST `/api/v1/landmarks/recognize` |
| POST `/api/v1/itinerary/generate` | POST `/api/v1/itineraries/generate` |
| GET `/api/v1/itinerary/history` | GET `/api/v1/itineraries` |

## Quality Requirements

- Async database access with connection pooling
- ML inference offloaded via thread pool (non-blocking)
- Repository pattern for data access
- Layered architecture: api → services → repositories → models
- Input validation on all endpoints
- File upload validation (content type + size)
- CORS configured for frontend origins
- Exception handling with appropriate HTTP status codes
- Type hints throughout

## Security Requirements

- Password hashing with bcrypt
- JWT secret from environment (min 32 chars)
- SQL injection protection via ORM
- Upload size limits and allowed MIME types
- No secrets committed to version control (`.gitignore`)

## Non-Functional Deliverables

- All endpoints documented in Swagger (`/docs`)
- Docker Compose one-command startup
- `.env.example` documenting required environment variables
- Demo seed script (`python -m app.seed`)

## Out of Scope (v1)

- Frontend application
- Google Cloud Vision API (LLM vision used instead)
- Email verification flow
- Automated test suite (planned)
