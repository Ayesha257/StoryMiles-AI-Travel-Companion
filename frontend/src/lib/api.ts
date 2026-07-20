const API_BASE_URL = (import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1").replace(/\/$/, "");

export type Tokens = {
  access_token: string;
  refresh_token: string;
  token_type: string;
};

export type User = {
  id: string;
  email: string;
  is_active: boolean;
  is_verified: boolean;
  profile?: {
    first_name?: string | null;
    last_name?: string | null;
  } | null;
};

export type AlbumPhoto = {
  id: string;
  image_id: string;
  filename: string;
  content_type: string;
  public_url: string;
  caption: string | null;
  position: number;
  created_at: string;
  updated_at: string;
};

export type TripAlbum = {
  id: string;
  user_id: string;
  title: string;
  destination: string | null;
  description: string | null;
  trip_start: string | null;
  trip_end: string | null;
  photos: AlbumPhoto[];
  created_at: string;
  updated_at: string;
};

export type AlbumCreate = {
  title: string;
  destination?: string;
  description?: string;
  trip_start?: string;
  trip_end?: string;
};

export type RecommendationRequest = {
  prompt: string;
  trip_days: number;
  budget_level: "low" | "medium" | "high";
  weather_preference: "hot" | "mild" | "cold";
  interests: string[];
  top_n?: number;
};

export type Recommendation = {
  name: string;
  country: string;
  city?: string | null;
  description: string;
  reasons: string[];
  best_time_to_visit: string;
  estimated_daily_budget: string;
  highlights: string[];
  predicted_score: number;
  explanation: string;
};

export type RecommendationResponse = {
  id: string;
  prompt: string;
  recommendations: Recommendation[];
  model: string;
  status: string;
  created_at: string;
};

export type Itinerary = {
  id: string;
  title: string;
  summary?: string | null;
  status: string;
  generated_by_model?: string | null;
  itinerary_data: {
    summary?: string;
    days?: Array<{
      day: number;
      title?: string;
      activities?: Array<{
        time?: string;
        activity?: string;
        location?: string;
        estimated_cost?: string;
        tips?: string[];
      }>;
      meals?: string[];
      transportation?: string;
      daily_budget?: string;
    }>;
    total_estimated_budget?: string;
    packing_tips?: string[];
    travel_tips?: string[];
  };
};

export type LandmarkResult = {
  id: string;
  public_url: string;
  landmark_name?: string | null;
  location?: string | null;
  country?: string | null;
  confidence?: number | null;
  description?: string | null;
  historical_background?: string | null;
  historical_facts?: string[];
  architecture_style?: string | null;
  built_year?: string | null;
  why_it_matters?: string | null;
  visitor_tips?: string[];
  best_time_to_visit?: string | null;
  nearby_highlights?: string[];
};

const TOKEN_KEY = "storymiles.tokens";

export function getTokens(): Tokens | null {
  if (typeof window === "undefined") return null;
  const value = window.localStorage.getItem(TOKEN_KEY);
  if (!value) return null;
  try {
    return JSON.parse(value) as Tokens;
  } catch {
    window.localStorage.removeItem(TOKEN_KEY);
    return null;
  }
}

export function setTokens(tokens: Tokens | null) {
  if (typeof window === "undefined") return;
  if (tokens) window.localStorage.setItem(TOKEN_KEY, JSON.stringify(tokens));
  else window.localStorage.removeItem(TOKEN_KEY);
}

async function parseError(response: Response): Promise<string> {
  try {
    const body = await response.json();
    if (typeof body.detail === "string") return body.detail;
    if (Array.isArray(body.detail)) return body.detail.map((item: { msg?: string }) => item.msg).filter(Boolean).join(", ");
  } catch {
    // Use the HTTP status below when the server did not return JSON.
  }
  return `Request failed (${response.status})`;
}

async function refreshAccessToken(): Promise<Tokens | null> {
  const current = getTokens();
  if (!current?.refresh_token) return null;
  const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: current.refresh_token }),
  });
  if (!response.ok) {
    setTokens(null);
    return null;
  }
  const tokens = (await response.json()) as Tokens;
  setTokens(tokens);
  return tokens;
}

export async function apiRequest<T>(
  path: string,
  init: RequestInit = {},
  retry = true,
): Promise<T> {
  const tokens = getTokens();
  const headers = new Headers(init.headers);
  if (!(init.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  if (tokens?.access_token) headers.set("Authorization", `Bearer ${tokens.access_token}`);

  const response = await fetch(`${API_BASE_URL}${path}`, { ...init, headers });
  if (response.status === 401 && retry && tokens?.refresh_token) {
    const refreshed = await refreshAccessToken();
    if (refreshed) return apiRequest<T>(path, init, false);
  }
  if (!response.ok) throw new Error(await parseError(response));
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export const api = {
  login: (email: string, password: string) =>
    apiRequest<Tokens>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
  register: (email: string, password: string, firstName?: string) =>
    apiRequest<{ email: string; message: string; verification_required: boolean }>("/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password, first_name: firstName || null }),
    }),
  verifyEmail: (email: string, code: string) =>
    apiRequest<{ message: string }>("/auth/verify-email", {
      method: "POST",
      body: JSON.stringify({ email, code }),
    }),
  resendVerification: (email: string) =>
    apiRequest<{ message: string }>("/auth/resend-verification", {
      method: "POST",
      body: JSON.stringify({ email }),
    }),
  forgotPassword: (email: string) =>
    apiRequest<{ message: string }>("/auth/forgot-password", {
      method: "POST",
      body: JSON.stringify({ email }),
    }),
  resetPassword: (email: string, code: string, newPassword: string) =>
    apiRequest<{ message: string }>("/auth/reset-password", {
      method: "POST",
      body: JSON.stringify({ email, code, new_password: newPassword }),
    }),
  me: () => apiRequest<User>("/users/me"),
  recommendations: (request: RecommendationRequest) =>
    apiRequest<RecommendationResponse>("/recommendations/generate", {
      method: "POST",
      body: JSON.stringify(request),
    }),
  generateItinerary: (request: {
    destination: string;
    country?: string;
    days: number;
    budget_level?: "low" | "medium" | "high";
    interests?: string[];
  }) =>
    apiRequest<Itinerary>("/itineraries/generate", {
      method: "POST",
      body: JSON.stringify(request),
    }),
  itinerary: (id: string) => apiRequest<Itinerary>(`/itineraries/${id}`),
  recognizeLandmark: (file: File) => {
    const body = new FormData();
    body.append("file", file);
    return apiRequest<LandmarkResult>("/landmarks/recognize", { method: "POST", body });
  },
  albums: () => apiRequest<TripAlbum[]>("/albums"),
  createAlbum: (request: AlbumCreate) =>
    apiRequest<TripAlbum>("/albums", {
      method: "POST",
      body: JSON.stringify(request),
    }),
  uploadAlbumPhotos: (albumId: string, files: File[]) => {
    const body = new FormData();
    files.forEach((file) => body.append("files", file));
    return apiRequest<AlbumPhoto[]>(`/albums/${albumId}/photos`, { method: "POST", body });
  },
  deleteAlbum: (albumId: string) =>
    apiRequest<void>(`/albums/${albumId}`, { method: "DELETE" }),
  downloadAlbumPdf: async (albumId: string) => {
    const tokens = getTokens();
    const response = await fetch(`${API_BASE_URL}/albums/${albumId}/pdf`, {
      headers: tokens?.access_token
        ? { Authorization: `Bearer ${tokens.access_token}` }
        : undefined,
    });
    if (!response.ok) throw new Error(await parseError(response));
    return response.blob();
  },
};

export function mediaUrl(path: string) {
  if (/^https?:\/\//i.test(path)) return path;
  return `${API_BASE_URL.replace(/\/api\/v1$/, "")}${path.startsWith("/") ? path : `/${path}`}`;
}

export { API_BASE_URL };
