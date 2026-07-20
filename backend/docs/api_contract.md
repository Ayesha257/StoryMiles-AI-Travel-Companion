# API Contract

Base URL

/api/v1

Authentication

POST /auth/register

Input

- full_name
- email
- password

Output

- user
- access_token
- refresh_token

---

POST /auth/login

Input

- email
- password

Output

- access_token
- refresh_token

---

GET /users/me

Requires JWT

Returns authenticated user.

---

POST /preferences

Stores user travel preferences.

---

GET /recommendations

Returns AI-generated destination recommendations.

---

POST /landmark/identify

Accepts image.

Returns identified landmark.

---

POST /itinerary/generate

Input

- destination
- days
- interests
- budget

Output

Generated itinerary.

---

GET /itinerary/history

Returns saved itineraries.