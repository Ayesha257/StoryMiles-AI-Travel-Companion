import { createFileRoute, Link } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { Sunrise, Sun, Moon, RefreshCw, ChevronDown } from "lucide-react";
import { ApiError, api, formatRetryAfter, friendlyApiMessage, type Itinerary } from "../lib/api";
import { useAuth } from "../lib/auth";

export const Route = createFileRoute("/itinerary/$id")({
  component: ItineraryPage,
  head: () => ({ meta: [{ title: "Itinerary — StoryMiles" }] }),
});

type Activity = { time: "morning" | "afternoon" | "evening"; title: string; description: string; category: string };
type Day = { dayNumber: number; activities: Activity[] };

type SelectedDestination = { name: string; country: string; image: string };

function normalizeTime(value?: string): Activity["time"] {
  const time = value?.toLowerCase() || "";
  if (time.includes("morning") || time.includes("am")) return "morning";
  if (time.includes("evening") || time.includes("night") || time.includes("pm")) return "evening";
  return "afternoon";
}

function toDays(itinerary: Itinerary): Day[] {
  return (itinerary.itinerary_data.days || []).map((day, index) => ({
    dayNumber: day.day || index + 1,
    activities: (day.activities || []).map((activity) => ({
      time: normalizeTime(activity.time),
      title: activity.activity || "Explore",
      description: [
        activity.location,
        activity.estimated_cost && `Estimated cost: ${activity.estimated_cost}`,
        ...(activity.tips || []),
      ].filter(Boolean).join(" · "),
      category: day.title || "Activity",
    })),
  }));
}

function ItineraryPage() {
  Route.useParams();
  const { user, loading: authLoading } = useAuth();
  const [hero, setHero] = useState<SelectedDestination>({
    name: "Your destination",
    country: "",
    image: "https://picsum.photos/seed/travel/1600/800",
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [retryAfterSeconds, setRetryAfterSeconds] = useState<number | null>(null);
  const [itinerary, setItinerary] = useState<Itinerary | null>(null);
  const [days, setDays] = useState<Day[]>([]);
  const [expanded, setExpanded] = useState<Set<number>>(new Set([1]));
  const [editing, setEditing] = useState(false);
  const [genDay, setGenDay] = useState(1);
  const [totalDays, setTotalDays] = useState(5);

  useEffect(() => {
    if (authLoading) return;
    const storedDestination = window.sessionStorage.getItem("storymiles.destination");
    if (!user || !storedDestination) {
      setLoading(false);
      return;
    }
    const selected = JSON.parse(storedDestination) as SelectedDestination;
    setHero(selected);
    const plan = JSON.parse(window.localStorage.getItem("storymiles.plan") || "{}");
    const requestedDays = Number(plan.trip_days) || 5;
    setTotalDays(requestedDays);
    const interval = window.setInterval(() => setGenDay((day) => (day % requestedDays) + 1), 500);
    api.generateItinerary({
      destination: selected.name,
      country: selected.country,
      days: requestedDays,
      budget_level: plan.budget_level,
      interests: plan.interests || [],
    })
      .then((result) => {
        setItinerary(result);
        const generatedDays = toDays(result);
        setDays(generatedDays);
        setExpanded(new Set(generatedDays.map((day) => day.dayNumber)));
      })
      .catch((cause) => {
        setRetryAfterSeconds(cause instanceof ApiError ? (cause.retryAfter ?? null) : null);
        setError(
          friendlyApiMessage(
            cause,
            "We couldn't generate your itinerary right now. Please try again in a few minutes.",
          ),
        );
      })
      .finally(() => {
        window.clearInterval(interval);
        setLoading(false);
      });
    return () => window.clearInterval(interval);
  }, [authLoading, user]);

  const toggleDay = (n: number) => {
    const next = new Set(expanded);
    if (next.has(n)) next.delete(n); else next.add(n);
    setExpanded(next);
  };

  return (
    <div>
      {/* Hero banner */}
      <div className="mx-auto max-w-6xl px-5 pt-6">
        <div className="relative h-64 md:h-80 overflow-hidden rounded-3xl shadow-xl">
          <img src={hero.image} alt={hero.name} className="absolute inset-0 w-full h-full object-cover" />
          <div className="absolute inset-0 bg-gradient-to-t from-ink/90 via-ink/45 to-transparent" />
          <div className="relative h-full flex flex-col justify-end px-6 md:px-10 pb-8 text-horizon">
            <div className="label-mono !text-horizon/70">A day-by-day plan</div>
            <h1 className="mt-2 font-display italic text-5xl md:text-7xl !text-horizon drop-shadow">{hero.name}</h1>
            <div className="label-mono mt-3 !text-horizon/80">{hero.country} · {days.length} days · Spring</div>
          </div>
        </div>
      </div>

      <div className="mx-auto max-w-6xl px-5 py-12">
        {loading ? (
          <LoadingReadout day={genDay} total={totalDays} />
        ) : !user ? (
          <div className="ticket-card max-w-md mx-auto text-center">
            <h2 className="font-display text-2xl">Sign in to build an itinerary</h2>
            <Link to="/auth" className="btn-primary mt-5">Sign in</Link>
          </div>
        ) : error ? (
          <div className="ticket-card max-w-md mx-auto text-center">
            <div className="label-mono">Temporary delay</div>
            <h2 className="font-display text-2xl mt-2">We couldn't generate your itinerary right now</h2>
            <p className="mt-3 text-sm text-charcoal/75">{error}</p>
            <p className="mt-2 text-xs text-charcoal/50">
              {retryAfterSeconds
                ? `Please wait about ${formatRetryAfter(retryAfterSeconds)} before trying again.`
                : "Please try again in a few minutes — our trip planner may be catching up."}
            </p>
            <div className="mt-5 flex flex-wrap gap-2 justify-center">
              <button
                type="button"
                className="btn-primary"
                onClick={() => window.location.reload()}
              >
                Try again
              </button>
              <Link to="/recommendations" className="btn-secondary">Back to recommendations</Link>
            </div>
          </div>
        ) : days.length === 0 ? (
          <div className="ticket-card max-w-md mx-auto text-center">
            <h2 className="font-display text-2xl">Choose a destination first</h2>
            <Link to="/recommendations" className="btn-primary mt-5">View recommendations</Link>
          </div>
        ) : (
          <>
            <div className="flex items-center justify-between flex-wrap gap-3 mb-8">
              <div className="flex gap-2">
                <button
                  className="btn-ghost text-sm"
                  onClick={() => setExpanded(new Set(expanded.size === days.length ? [] : days.map((d) => d.dayNumber)))}
                >
                  {expanded.size === days.length ? "Collapse all" : "Expand all"}
                </button>
                <button
                  className="btn-ghost text-sm"
                  onClick={() => setEditing((v) => !v)}
                >
                  {editing ? "Done editing" : "Edit itinerary"}
                </button>
              </div>
            </div>

            <div className="relative">
              {/* vertical dashed timeline */}
              <div className="absolute left-6 top-0 bottom-0 border-l-2 border-dashed border-ink/15 hidden md:block" />
              <ol className="space-y-6">
                {days.map((day) => (
                  <li key={day.dayNumber} className="md:pl-20 relative">
                    {/* day marker */}
                    <div className="hidden md:flex absolute left-0 top-4 w-12 h-12 rounded-full bg-ink text-horizon items-center justify-center flex-col leading-none shadow-lg ring-4 ring-horizon">
                      <div className="text-[9px] tracking-widest opacity-70">DAY</div>
                      <div className="font-display text-lg">{String(day.dayNumber).padStart(2, "0")}</div>
                    </div>

                    <div className="ticket-card">
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="label-mono md:hidden">Day {String(day.dayNumber).padStart(2, "0")}</div>
                          <h3 className="font-display text-2xl mt-1">Day {day.dayNumber}</h3>
                        </div>
                        <div className="flex items-center gap-1">
                          <button
                            className="btn-ghost !p-2"
                            aria-label={`Regenerate day ${day.dayNumber}`}
                            onClick={() => console.log("regen day", day.dayNumber)}
                          >
                            <RefreshCw size={16} />
                          </button>
                          <button
                            className="btn-ghost !p-2 md:hidden"
                            onClick={() => toggleDay(day.dayNumber)}
                            aria-label="Toggle day"
                          >
                            <ChevronDown size={18} className={`transition ${expanded.has(day.dayNumber) ? "rotate-180" : ""}`} />
                          </button>
                        </div>
                      </div>

                      <div className={`${expanded.has(day.dayNumber) ? "block" : "hidden"} md:block mt-4 space-y-4`}>
                        {day.activities.map((a, i) => (
                          <ActivityRow key={i} a={a} editing={editing} />
                        ))}
                      </div>
                    </div>
                  </li>
                ))}
              </ol>
            </div>

            <div className="mt-12 flex flex-wrap gap-3 justify-end">
              <Link to="/plan" className="btn-secondary">Start a new trip</Link>
              <span className="btn-primary" aria-label="Itinerary saved">
                Saved{itinerary?.generated_by_model ? ` · ${itinerary.generated_by_model}` : ""}
              </span>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

const timeIcons = { morning: Sunrise, afternoon: Sun, evening: Moon };

function ActivityRow({ a, editing }: { a: Activity; editing: boolean }) {
  const Icon = timeIcons[a.time];
  const [title, setTitle] = useState(a.title);
  const [desc, setDesc] = useState(a.description);
  return (
    <div className="flex gap-4">
      <div className="shrink-0 w-9 h-9 rounded-xl bg-stamp text-ink flex items-center justify-center">
        <Icon size={17} />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-baseline justify-between gap-3">
          {editing ? (
            <input
              className="font-medium bg-transparent border-b border-ink/30 focus:border-poppy outline-none w-full"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />
          ) : (
            <div className="font-medium">{title}</div>
          )}
          <span className="tag shrink-0">{a.category}</span>
        </div>
        {editing ? (
          <textarea
            className="mt-1 text-sm text-charcoal/75 w-full bg-transparent border border-ink/15 rounded p-2 focus:border-poppy outline-none"
            value={desc}
            onChange={(e) => setDesc(e.target.value)}
            rows={2}
          />
        ) : (
          <p className="mt-1 text-sm text-charcoal/75">{desc}</p>
        )}
      </div>
    </div>
  );
}

function LoadingReadout({ day, total }: { day: number; total: number }) {
  return (
    <div className="py-16 text-center">
      <div className="label-mono">Generating itinerary</div>
      <div className="mt-4 font-mono text-2xl md:text-3xl text-ink">
        Planning day {String(day).padStart(2, "0")} of {String(total).padStart(2, "0")}…
      </div>
      <svg viewBox="0 0 600 60" className="mt-8 mx-auto max-w-xl w-full">
        <path
          d="M20,30 Q150,0 300,30 T580,30"
          fill="none"
          stroke="var(--poppy)"
          strokeWidth="2"
          strokeDasharray="6 6"
          strokeLinecap="round"
          className="draw-line"
          style={{ ["--dash-len" as string]: "700" }}
        />
      </svg>
    </div>
  );
}
