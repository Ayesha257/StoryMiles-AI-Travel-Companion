import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useMemo, useState } from "react";
import { Check, ChevronLeft, ChevronRight, Sun, Cloud, Snowflake, Shuffle } from "lucide-react";
import { api, friendlyApiMessage, type RecommendationRequest } from "../lib/api";
import { useAuth } from "../lib/auth";

export const Route = createFileRoute("/plan")({
  component: PlanPage,
  head: () => ({ meta: [{ title: "Plan your trip — StoryMiles" }] }),
});

type Prefs = {
  budget: string | null;
  interests: string[];
  weatherPref: string | null;
  duration: number;
};

const budgetTiers = [
  { key: "budget", label: "Budget", range: "< €80 / day" },
  { key: "mid", label: "Mid-range", range: "€80 – €180 / day" },
  { key: "comfort", label: "Comfort", range: "€180 – €350 / day" },
  { key: "luxury", label: "Luxury", range: "€350+ / day" },
];
const interestOptions = ["Adventure", "Beach", "History", "Food", "Nightlife", "Nature", "Shopping", "Wellness"];
const weatherOptions = [
  { key: "warm", label: "Warm", Icon: Sun },
  { key: "mild", label: "Mild", Icon: Cloud },
  { key: "cold", label: "Cold", Icon: Snowflake },
  { key: "any", label: "Any", Icon: Shuffle },
];
const stepTitles = ["Budget", "Interests", "Weather", "Duration"];

function PlanPage() {
  const nav = useNavigate();
  const { user } = useAuth();
  const [step, setStep] = useState(0);
  const [prefs, setPrefs] = useState<Prefs>({ budget: null, interests: [], weatherPref: null, duration: 7 });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const canContinue = useMemo(() => {
    if (step === 0) return !!prefs.budget;
    if (step === 1) return prefs.interests.length > 0;
    if (step === 2) return !!prefs.weatherPref;
    return prefs.duration >= 3;
  }, [step, prefs]);

  const isLast = step === 3;

  const submitPreferences = async () => {
    const request: RecommendationRequest = {
      prompt: `Recommend destinations for a ${prefs.duration}-day trip focused on ${prefs.interests.join(", ")}.`,
      trip_days: prefs.duration,
      budget_level: prefs.budget === "budget" ? "low" : prefs.budget === "mid" ? "medium" : "high",
      weather_preference: prefs.weatherPref === "warm" ? "hot" : prefs.weatherPref === "cold" ? "cold" : "mild",
      interests: prefs.interests.map((interest) => interest.toLowerCase()),
      top_n: 8,
    };
    window.localStorage.setItem("storymiles.plan", JSON.stringify(request));
    if (!user) {
      await nav({ to: "/auth" });
      return;
    }
    setSubmitting(true);
    setError("");
    try {
      const response = await api.recommendations(request);
      window.sessionStorage.setItem("storymiles.recommendations", JSON.stringify(response));
      await nav({ to: "/recommendations" });
    } catch (cause) {
      setError(
        friendlyApiMessage(
          cause,
          "We couldn't load personalized matches right now. Please try again in a few minutes.",
        ),
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="mx-auto max-w-3xl px-5 py-12 md:py-20">
      <div className="eyebrow">Step {step + 1} of 4</div>
      <h1 className="mt-3 font-display text-3xl md:text-5xl">Let's shape your trip.</h1>
      <p className="mt-4 text-charcoal/70 max-w-md">Four quick questions. You can edit anything later.</p>

      {/* Step progress strip */}
      <div className="mt-9 grid grid-cols-4 gap-2">
        {stepTitles.map((t, i) => {
          const done = i < step;
          const active = i === step;
          return (
            <div key={t} className="text-center">
              <div
                className={`h-1.5 rounded-full transition-colors duration-300 ${
                  active ? "bg-poppy" : done ? "bg-marigold" : "bg-ink/10"
                }`}
              />
              <div
                className={`mt-2 text-xs font-medium flex items-center justify-center gap-1 ${
                  active ? "text-poppy" : done ? "text-ink" : "text-ink/40"
                }`}
              >
                {done && <Check size={13} />} {t}
              </div>
            </div>
          );
        })}
      </div>

      <div key={step} className="mt-8 ticket-card stamp-in">
        {step === 0 && <BudgetStep prefs={prefs} setPrefs={setPrefs} />}
        {step === 1 && <InterestsStep prefs={prefs} setPrefs={setPrefs} />}
        {step === 2 && <WeatherStep prefs={prefs} setPrefs={setPrefs} />}
        {step === 3 && <DurationStep prefs={prefs} setPrefs={setPrefs} />}
      </div>

      <div className="mt-8 flex items-center justify-between">
        <button
          className="btn-secondary"
          onClick={() => setStep((s) => Math.max(0, s - 1))}
          disabled={step === 0}
        >
          <ChevronLeft size={16} /> Back
        </button>
        <button
          className="btn-primary"
          disabled={!canContinue}
          onClick={async () => {
            if (isLast) {
              await submitPreferences();
              return;
            }
            setStep((s) => s + 1);
          }}
        >
          {submitting ? "Finding matches…" : isLast ? "Find my destinations" : "Continue"} <ChevronRight size={16} />
        </button>
      </div>
      {error && (
        <div className="mt-4 ticket-card !p-4">
          <div className="label-mono">Couldn't load matches</div>
          <p className="mt-2 text-sm text-charcoal/80">{error}</p>
        </div>
      )}
    </div>
  );
}

function BudgetStep({ prefs, setPrefs }: { prefs: Prefs; setPrefs: (p: Prefs) => void }) {
  return (
    <div>
      <h2 className="font-display text-2xl">What's your comfort with spending?</h2>
      <p className="text-sm text-charcoal/70 mt-1">Pick a tier — we'll build the days around it.</p>
      <div className="mt-6 grid sm:grid-cols-2 gap-3">
        {budgetTiers.map((t) => {
          const on = prefs.budget === t.key;
          return (
            <button
              key={t.key}
              onClick={() => setPrefs({ ...prefs, budget: t.key })}
              className={`text-left rounded-2xl p-4 border-2 transition shadow-sm ${
                on
                  ? "border-poppy bg-poppy/5 stamp-in"
                  : "border-ink/10 bg-white hover:border-ink/30 hover:-translate-y-0.5"
              }`}
            >
              <div className="font-display text-xl">{t.label}</div>
              <div className="label-mono mt-1">{t.range}</div>
            </button>
          );
        })}
      </div>
    </div>
  );
}

function InterestsStep({ prefs, setPrefs }: { prefs: Prefs; setPrefs: (p: Prefs) => void }) {
  const toggle = (i: string) => {
    const set = new Set(prefs.interests);
    if (set.has(i)) set.delete(i); else set.add(i);
    setPrefs({ ...prefs, interests: Array.from(set) });
  };
  const palette = ["sage", "marigold", "poppy"];
  return (
    <div>
      <h2 className="font-display text-2xl">What do you love doing?</h2>
      <p className="text-sm text-charcoal/70 mt-1">Pick as many as fit.</p>
      <div className="mt-6 flex flex-wrap gap-2">
        {interestOptions.map((opt, i) => {
          const on = prefs.interests.includes(opt);
          const color = palette[i % palette.length];
          return (
            <button
              key={opt}
              onClick={() => toggle(opt)}
              className={`px-4 py-2 rounded-full border-2 text-sm font-medium transition flex items-center gap-1.5 shadow-sm ${
                on ? `tag--${color} border-transparent` : "border-ink/15 bg-white hover:border-ink/40"
              }`}
            >
              {on && <Check size={14} />} {opt}
            </button>
          );
        })}
      </div>
    </div>
  );
}

function WeatherStep({ prefs, setPrefs }: { prefs: Prefs; setPrefs: (p: Prefs) => void }) {
  return (
    <div>
      <h2 className="font-display text-2xl">What weather are you in the mood for?</h2>
      <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-3">
        {weatherOptions.map((w) => {
          const on = prefs.weatherPref === w.key;
          return (
            <button
              key={w.key}
              onClick={() => setPrefs({ ...prefs, weatherPref: w.key })}
              className={`rounded-2xl p-6 border-2 flex flex-col items-center gap-3 transition shadow-sm ${
                on
                  ? "border-poppy bg-poppy/5 stamp-in"
                  : "border-ink/10 bg-white hover:border-ink/30 hover:-translate-y-0.5"
              }`}
            >
              <w.Icon size={32} className={on ? "text-poppy" : "text-ink"} />
              <div className="font-medium">{w.label}</div>
            </button>
          );
        })}
      </div>
    </div>
  );
}

function DurationStep({ prefs, setPrefs }: { prefs: Prefs; setPrefs: (p: Prefs) => void }) {
  return (
    <div>
      <h2 className="font-display text-2xl">How long is the trip?</h2>
      <div className="mt-8 flex items-baseline gap-3">
        <div className="font-display text-7xl text-ink">{prefs.duration}</div>
        <div className="text-charcoal/70">days</div>
      </div>
      <input
        type="range"
        min={3}
        max={21}
        value={prefs.duration}
        onChange={(e) => setPrefs({ ...prefs, duration: parseInt(e.target.value) })}
        className="mt-6 w-full accent-poppy"
      />
      <div className="flex justify-between label-mono mt-2">
        <span>3 days</span>
        <span>21 days</span>
      </div>
    </div>
  );
}
