import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useEffect, useMemo } from "react";
import {
  Camera,
  Compass,
  Map,
  ArrowRight,
  CalendarDays,
  Wallet,
  Heart,
  Images,
  Sparkles,
  Globe2,
  Route as RouteIcon,
} from "lucide-react";
import { useAuth } from "../lib/auth";
import type { RecommendationRequest, RecommendationResponse } from "../lib/api";

export const Route = createFileRoute("/dashboard")({
  component: DashboardPage,
  head: () => ({ meta: [{ title: "Dashboard — StoryMiles" }] }),
});

const actions = [
  {
    to: "/plan" as const,
    title: "Plan a trip",
    body: "Four quick questions, then the model ranks destinations for you.",
    Icon: Map,
    img: "https://images.unsplash.com/photo-1488646953014-85cb44e25828?w=800&q=80",
  },
  {
    to: "/recommendations" as const,
    title: "Your matches",
    body: "Destinations scored against your budget, weather, and interests.",
    Icon: Compass,
    img: "https://images.unsplash.com/photo-1502920917128-1aa500764cbd?w=800&q=80",
  },
  {
    to: "/albums" as const,
    title: "Trip albums",
    body: "Collect your travel photos and turn them into a downloadable PDF keepsake.",
    Icon: Images,
    img: "https://images.unsplash.com/photo-1516979187457-637abb4f9353?w=800&q=80",
  },
  {
    to: "/scanner" as const,
    title: "Landmark scanner",
    body: "Upload a photo and find out what you're looking at, instantly.",
    Icon: Camera,
    img: "https://images.unsplash.com/photo-1499856871958-5b9627545d1a?w=800&q=80",
  },
];

function readPlan(): RecommendationRequest | null {
  try {
    const raw = window.localStorage.getItem("storymiles.plan");
    return raw ? (JSON.parse(raw) as RecommendationRequest) : null;
  } catch {
    return null;
  }
}

function readMatches(): RecommendationResponse | null {
  try {
    const raw = window.sessionStorage.getItem("storymiles.recommendations");
    return raw ? (JSON.parse(raw) as RecommendationResponse) : null;
  } catch {
    return null;
  }
}

function DashboardPage() {
  const navigate = useNavigate();
  const { user, loading } = useAuth();

  useEffect(() => {
    if (!loading && !user) {
      void navigate({ to: "/auth" });
    }
  }, [loading, user, navigate]);

  const plan = useMemo(() => (typeof window === "undefined" ? null : readPlan()), []);
  const matches = useMemo(() => (typeof window === "undefined" ? null : readMatches()), []);

  if (loading || !user) {
    return (
      <div className="mx-auto max-w-6xl px-5 py-20">
        <div className="label-mono">Loading…</div>
      </div>
    );
  }

  const name = user.profile?.first_name?.trim() || user.email.split("@")[0];
  const today = new Date().toLocaleDateString(undefined, {
    weekday: "long",
    month: "long",
    day: "numeric",
  });
  const topMatch = matches?.recommendations?.[0];

  return (
    <div className="mx-auto max-w-6xl px-5 py-8 md:py-12">
      {/* Hero banner */}
      <section className="relative overflow-hidden rounded-3xl bg-ink text-horizon shadow-xl">
        <img
          src="https://images.unsplash.com/photo-1476514525535-07fb3b4ae5f1?w=1600&q=80"
          alt=""
          aria-hidden
          className="absolute inset-0 w-full h-full object-cover opacity-35"
        />
        <div
          aria-hidden
          className="absolute inset-0"
          style={{
            background:
              "linear-gradient(105deg, rgba(16,38,61,0.95) 30%, rgba(16,38,61,0.55) 70%, rgba(16,38,61,0.25) 100%)",
          }}
        />
        <div className="relative px-6 md:px-10 py-10 md:py-14">
          <div className="label-mono !text-horizon/60">{today}</div>
          <h1 className="mt-3 font-display text-3xl md:text-5xl !text-horizon">
            Welcome back, <span className="italic text-marigold">{name}</span>
          </h1>
          <p className="mt-4 max-w-lg text-sm md:text-base text-horizon/75 leading-relaxed">
            Your travel desk is ready — pick up a plan, browse your matches, or
            identify a landmark from the road.
          </p>
          <div className="mt-7 flex flex-wrap gap-3">
            <Link to="/plan" className="btn-primary">
              {plan ? "Update my trip" : "Plan a new trip"} <ArrowRight size={16} />
            </Link>
            {matches && (
              <Link to="/recommendations" className="btn-secondary !bg-white/10 !text-horizon !border-horizon/30 hover:!bg-horizon hover:!text-ink">
                View matches
              </Link>
            )}
          </div>
        </div>
      </section>

      {/* Stats strip */}
      <section className="mt-6 grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          Icon={Globe2}
          label="Destinations in library"
          value="559"
          sub="Real city data"
        />
        <StatCard
          Icon={Sparkles}
          label="Your matches"
          value={matches ? String(matches.recommendations.length) : "—"}
          sub={topMatch ? `Top pick: ${topMatch.name}` : "Plan a trip to get matches"}
        />
        <StatCard
          Icon={CalendarDays}
          label="Trip length"
          value={plan ? `${plan.trip_days} days` : "—"}
          sub={plan ? "From your saved plan" : "Not set yet"}
        />
        <StatCard
          Icon={Wallet}
          label="Budget level"
          value={plan ? capitalize(plan.budget_level) : "—"}
          sub={plan ? `Weather: ${capitalize(plan.weather_preference)}` : "Not set yet"}
        />
      </section>

      {/* Saved preferences */}
      {plan && (
        <section className="mt-6 ticket-card flex flex-wrap items-center justify-between gap-5">
          <div className="flex items-start gap-4 min-w-0">
            <div className="w-11 h-11 shrink-0 rounded-2xl bg-poppy/10 text-poppy flex items-center justify-center">
              <Heart size={20} />
            </div>
            <div className="min-w-0">
              <div className="label-mono">Your travel style</div>
              <div className="mt-2 flex flex-wrap gap-1.5">
                {plan.interests.map((interest, i) => (
                  <span
                    key={interest}
                    className={`tag tag--${["sage", "marigold", "poppy"][i % 3]}`}
                  >
                    {capitalize(interest)}
                  </span>
                ))}
              </div>
            </div>
          </div>
          <Link to="/plan" className="btn-secondary !py-2 !px-4 text-sm shrink-0">
            Edit preferences
          </Link>
        </section>
      )}

      {/* Action cards */}
      <section className="mt-10">
        <div className="flex items-end justify-between gap-4">
          <div>
            <div className="eyebrow">Quick actions</div>
            <h2 className="mt-2 font-display text-2xl md:text-3xl">Where to next?</h2>
          </div>
        </div>
        <div className="mt-6 grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {actions.map((action) => (
            <Link
              key={action.to}
              to={action.to}
              className="ticket-card ticket-card--hoverable !p-0 group flex flex-col overflow-hidden"
            >
              <div className="card-img relative h-36">
                <img src={action.img} alt="" className="w-full h-full object-cover" loading="lazy" />
                <div className="absolute inset-0 bg-gradient-to-t from-ink/50 to-transparent" />
                <div className="absolute bottom-3 left-4 w-10 h-10 rounded-xl bg-white/95 text-ink flex items-center justify-center shadow-md">
                  <action.Icon size={19} />
                </div>
              </div>
              <div className="flex flex-col flex-1 p-5">
                <h3 className="font-display text-xl">{action.title}</h3>
                <p className="mt-1.5 text-sm text-charcoal/70 leading-relaxed flex-1">
                  {action.body}
                </p>
                <div className="mt-4 inline-flex items-center gap-1.5 text-sm font-semibold text-poppy group-hover:gap-2.5 transition-all">
                  Open <ArrowRight size={15} />
                </div>
              </div>
            </Link>
          ))}
        </div>
      </section>

      {/* Top matches preview */}
      {matches && matches.recommendations.length > 0 && (
        <section className="mt-10">
          <div className="flex items-end justify-between gap-4">
            <div>
              <div className="eyebrow">From your last plan</div>
              <h2 className="mt-2 font-display text-2xl md:text-3xl">Top matches</h2>
            </div>
            <Link to="/recommendations" className="btn-ghost text-sm">
              See all <ArrowRight size={15} />
            </Link>
          </div>
          <div className="mt-6 grid sm:grid-cols-3 gap-5">
            {matches.recommendations.slice(0, 3).map((match) => (
              <Link
                key={match.name}
                to="/recommendations"
                className="ticket-card ticket-card--hoverable !p-0 overflow-hidden group"
              >
                <div className="card-img relative h-32">
                  <img
                    src={`https://picsum.photos/seed/${encodeURIComponent(match.name)}/600/360`}
                    alt={match.name}
                    className="w-full h-full object-cover"
                    loading="lazy"
                  />
                  <div className="absolute top-2.5 right-2.5 score-badge !w-11 !h-11">
                    <span className="font-display text-sm">
                      {Math.round(Math.max(0, Math.min(1, match.predicted_score)) * 100)}
                    </span>
                    <span className="text-[7px] tracking-widest opacity-70">MATCH</span>
                  </div>
                </div>
                <div className="p-4">
                  <div className="font-display italic text-lg text-ink">{match.name}</div>
                  <div className="label-mono mt-0.5">{match.country}</div>
                </div>
              </Link>
            ))}
          </div>
        </section>
      )}

      {/* Account footer card */}
      <section className="mt-10 ticket-card !bg-stamp/60 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-full bg-ink text-horizon flex items-center justify-center font-display text-lg italic">
            {name.charAt(0).toUpperCase()}
          </div>
          <div>
            <div className="font-medium text-ink">{name}</div>
            <div className="text-sm text-charcoal/60">{user.email}</div>
          </div>
        </div>
        <div className="flex items-center gap-2 text-sm text-charcoal/60">
          <RouteIcon size={16} className="text-sage" />
          Every mile tells a story.
        </div>
      </section>
    </div>
  );
}

function StatCard({
  Icon,
  label,
  value,
  sub,
}: {
  Icon: typeof Globe2;
  label: string;
  value: string;
  sub: string;
}) {
  return (
    <div className="ticket-card !p-5">
      <div className="flex items-center gap-2.5">
        <div className="w-8 h-8 rounded-lg bg-ink/6 text-ink flex items-center justify-center">
          <Icon size={16} />
        </div>
        <span className="label-mono !text-[0.62rem]">{label}</span>
      </div>
      <div className="mt-3 font-display text-3xl text-ink">{value}</div>
      <div className="mt-1 text-xs text-charcoal/55 truncate">{sub}</div>
    </div>
  );
}

function capitalize(value: string) {
  return value.charAt(0).toUpperCase() + value.slice(1);
}
