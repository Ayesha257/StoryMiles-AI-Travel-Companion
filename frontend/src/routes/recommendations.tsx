import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { api, friendlyApiMessage, type RecommendationRequest, type RecommendationResponse } from "../lib/api";
import { useAuth } from "../lib/auth";

export const Route = createFileRoute("/recommendations")({
  component: RecommendationsPage,
  head: () => ({ meta: [{ title: "Matched destinations — StoryMiles" }] }),
});

type TagColor = "sage" | "marigold" | "poppy";
type Dest = {
  id: string;
  name: string;
  country: string;
  image: string;
  matchScore: number;
  tags: [string, TagColor][];
  description: string;
  avgBudget: string;
  bestSeason: string;
};

const tagColors = ["sage", "marigold", "poppy"] as const;

function toDestinations(response: RecommendationResponse): Dest[] {
  return response.recommendations.map((item, index) => ({
    id: `${item.name.toLowerCase().replace(/[^a-z0-9]+/g, "-")}-${index}`,
    name: item.name,
    country: item.country,
    image: `https://picsum.photos/seed/${encodeURIComponent(item.name)}/800/500`,
    matchScore: Math.round(Math.max(0, Math.min(1, item.predicted_score)) * 100),
    tags: item.highlights.map((tag, tagIndex) => [
      tag.charAt(0).toUpperCase() + tag.slice(1),
      tagColors[tagIndex % tagColors.length],
    ] as [string, TagColor]),
    description: item.description,
    avgBudget: item.estimated_daily_budget,
    bestSeason: item.best_time_to_visit,
  }));
}

function RecommendationsPage() {
  const { user, loading: authLoading } = useAuth();
  const [loading, setLoading] = useState(true);
  const [destinations, setDestinations] = useState<Dest[]>([]);
  const [error, setError] = useState("");
  const [activeTags, setActiveTags] = useState<Set<string>>(new Set());

  useEffect(() => {
    if (authLoading) return;
    if (!user) {
      setLoading(false);
      return;
    }
    const cached = window.sessionStorage.getItem("storymiles.recommendations");
    if (cached) {
      try {
        setDestinations(toDestinations(JSON.parse(cached) as RecommendationResponse));
        setLoading(false);
        return;
      } catch {
        window.sessionStorage.removeItem("storymiles.recommendations");
      }
    }
    const savedPlan = window.localStorage.getItem("storymiles.plan");
    if (!savedPlan) {
      setLoading(false);
      return;
    }
    api.recommendations(JSON.parse(savedPlan) as RecommendationRequest)
      .then((response) => {
        window.sessionStorage.setItem("storymiles.recommendations", JSON.stringify(response));
        setDestinations(toDestinations(response));
      })
      .catch((cause) =>
        setError(
          friendlyApiMessage(
            cause,
            "We couldn't load personalized matches right now. Please try again shortly.",
          ),
        ),
      )
      .finally(() => setLoading(false));
  }, [authLoading, user]);

  const allTags = Array.from(new Set(destinations.flatMap((d) => d.tags.map(([tag]) => tag))));
  const filtered = destinations.filter((d) =>
    activeTags.size === 0 || d.tags.some(([t]) => activeTags.has(t))
  );

  return (
    <div className="mx-auto max-w-6xl px-5 py-12 md:py-16">
      <div className="flex items-end justify-between gap-6 flex-wrap">
        <div>
          <div className="eyebrow">Your matches</div>
          <h1 className="mt-3 font-display text-4xl md:text-5xl">Matched for you</h1>
          <div className="label-mono mt-3">
            Ranked by the StoryMiles recommendation model
          </div>
        </div>
        <Link to="/plan" className="btn-secondary !py-2 !px-4 text-sm">
          Edit preferences
        </Link>
      </div>

      {/* Filter chips */}
      <div className="mt-8 flex flex-wrap gap-2">
        {allTags.map((t) => {
          const on = activeTags.has(t);
          return (
            <button
              key={t}
              onClick={() => {
                const next = new Set(activeTags);
                if (on) next.delete(t); else next.add(t);
                setActiveTags(next);
              }}
              className={`px-3.5 py-1.5 rounded-full text-sm font-medium border transition shadow-sm ${
                on ? "bg-ink text-horizon border-ink" : "bg-white border-ink/15 hover:border-ink/40"
              }`}
            >
              {t}
            </button>
          );
        })}
        {activeTags.size > 0 && (
          <button className="btn-ghost text-xs" onClick={() => setActiveTags(new Set())}>Clear</button>
        )}
      </div>

      {!authLoading && !user ? (
        <div className="mt-12 ticket-card max-w-md">
          <h2 className="font-display text-2xl">Sign in to see your matches</h2>
          <p className="mt-2 text-sm text-charcoal/70">Recommendations are generated from your trip preferences and saved to your account.</p>
          <Link to="/auth" className="btn-primary mt-5">Sign in</Link>
        </div>
      ) : error ? (
        <div className="mt-12 ticket-card max-w-md">
          <div className="label-mono">Temporary delay</div>
          <h2 className="font-display text-2xl mt-2">Matches are taking a break</h2>
          <p className="mt-2 text-sm text-charcoal/75">{error}</p>
          <Link to="/plan" className="btn-secondary mt-5">Try again from preferences</Link>
        </div>
      ) : loading ? (
        <SkeletonGrid />
      ) : filtered.length === 0 ? (
        <EmptyState onClear={() => setActiveTags(new Set())} />
      ) : (
        <div className="mt-10 grid sm:grid-cols-2 lg:grid-cols-3 gap-8">
          {filtered.map((d, i) => (
            <DestCard key={d.id} d={d} delay={i * 60} />
          ))}
        </div>
      )}
    </div>
  );
}

function DestCard({ d, delay }: { d: Dest; delay: number }) {
  const nav = useNavigate();
  return (
    <article
      className="ticket-card ticket-card--hoverable stamp-in !p-0 flex flex-col overflow-hidden"
      style={{ animationDelay: `${delay}ms` }}
    >
      <div className="card-img relative h-44">
        <img src={d.image} alt={d.name} className="w-full h-full object-cover" loading="lazy" />
        <div className="absolute top-3 right-3 score-badge">
          <div className="font-display text-lg">{d.matchScore}</div>
          <div className="text-[8px] tracking-widest opacity-70">MATCH</div>
        </div>
      </div>
      <div className="flex flex-col flex-1 p-5">
        <div className="flex items-baseline justify-between gap-2">
          <div className="font-display italic text-2xl text-ink">{d.name}</div>
          <div className="text-xs text-charcoal/55 font-medium">{d.country}</div>
        </div>
        <div className="flex flex-wrap gap-1.5 mt-3">
          {d.tags.map(([t, c]) => (
            <span key={t} className={`tag tag--${c}`}>{t}</span>
          ))}
        </div>
        <p className="text-sm mt-3 text-charcoal/70 leading-relaxed flex-1">{d.description}</p>
        <div className="ticket-divider" />
        <div className="flex items-center justify-between gap-3">
          <div className="label-mono truncate">
            {d.avgBudget} · {d.bestSeason}
          </div>
          <button
            className="btn-primary !py-2 !px-4 text-sm shrink-0"
            onClick={() => {
              window.sessionStorage.setItem("storymiles.destination", JSON.stringify(d));
              nav({ to: "/itinerary/$id", params: { id: d.id } });
            }}
          >
            Build itinerary
          </button>
        </div>
      </div>
    </article>
  );
}

function SkeletonGrid() {
  return (
    <div className="mt-10 grid sm:grid-cols-2 lg:grid-cols-3 gap-8">
      {Array.from({ length: 6 }).map((_, i) => (
        <div key={i} className="ticket-card !p-0 animate-pulse overflow-hidden">
          <div className="h-44 bg-ink/10" />
          <div className="p-5">
            <div className="h-6 bg-ink/10 w-2/3 rounded-lg" />
            <div className="h-3 bg-ink/10 w-full mt-4 rounded-lg" />
            <div className="h-3 bg-ink/10 w-5/6 mt-2 rounded-lg" />
            <div className="ticket-divider" />
            <div className="h-9 bg-ink/10 w-1/3 rounded-full" />
          </div>
        </div>
      ))}
    </div>
  );
}

function EmptyState({ onClear }: { onClear: () => void }) {
  return (
    <div className="mt-16 ticket-card max-w-md mx-auto text-center">
      <div className="label-mono">No matches</div>
      <h2 className="mt-2 font-display text-2xl">We couldn't find a match</h2>
      <p className="mt-3 text-sm text-charcoal/75">
        Try widening your budget, dropping a filter, or picking a couple more interests.
      </p>
      <div className="mt-5 flex gap-2 justify-center">
        <button className="btn-secondary" onClick={onClear}>Clear filters</button>
        <Link to="/plan" className="btn-primary">Edit preferences</Link>
      </div>
    </div>
  );
}
