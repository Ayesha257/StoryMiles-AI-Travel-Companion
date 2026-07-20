import { createFileRoute } from "@tanstack/react-router";
import { useRef, useState } from "react";
import { Camera, Clock3, Landmark, MapPin, Sparkles, Upload, X } from "lucide-react";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";

export const Route = createFileRoute("/scanner")({
  component: ScannerPage,
  head: () => ({ meta: [{ title: "Landmark Scanner — StoryMiles" }] }),
});

type Result = {
  name: string;
  location: string;
  country: string;
  confidence: number;
  summary: string;
  historicalBackground: string;
  historicalFacts: string[];
  architectureStyle: string;
  builtYear: string;
  whyItMatters: string;
  visitorTips: string[];
  bestTimeToVisit: string;
  nearbyHighlights: string[];
};

function ScannerPage() {
  const { user } = useAuth();
  const inputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [status, setStatus] = useState<"idle" | "loading" | "done" | "low">("idle");
  const [result, setResult] = useState<Result | null>(null);
  const [feedbackOpen, setFeedbackOpen] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const [error, setError] = useState("");

  const handleFile = (f: File | null) => {
    if (!f) return;
    setFile(f);
    setPreview(URL.createObjectURL(f));
    setStatus("idle");
    setResult(null);
    setError("");
  };

  const clear = () => {
    setFile(null);
    setPreview(null);
    setStatus("idle");
    setResult(null);
    setFeedbackOpen(false);
  };

  const identify = async () => {
    if (!file) return;
    if (!user) {
      setError("Sign in before scanning a landmark.");
      return;
    }
    setStatus("loading");
    setError("");
    try {
      const response = await api.recognizeLandmark(file);
      const r: Result = {
        name: response.landmark_name || "Not sure",
        location: response.location || "",
        country: response.country || "",
        confidence: Math.round((response.confidence || 0) * 100),
        summary: response.description || "",
        historicalBackground: response.historical_background || "",
        historicalFacts: response.historical_facts || [],
        architectureStyle: response.architecture_style || "",
        builtYear: response.built_year || "",
        whyItMatters: response.why_it_matters || "",
        visitorTips: response.visitor_tips || [],
        bestTimeToVisit: response.best_time_to_visit || "",
        nearbyHighlights: response.nearby_highlights || [],
      };
      setResult(r);
      setStatus(r.confidence < 60 ? "low" : "done");
    } catch (cause) {
      setStatus("idle");
      setError(cause instanceof Error ? cause.message : "The image could not be analyzed");
    }
  };

  return (
    <div className="mx-auto max-w-3xl px-5 py-12 md:py-20">
      <div className="eyebrow">Landmark scanner</div>
      <h1 className="mt-3 font-display text-4xl md:text-5xl">What are you looking at?</h1>
      <p className="mt-4 text-charcoal/75 max-w-lg leading-relaxed">
        Upload a photo and Gemini identifies the landmark, shares its history, and guides you through
        the details that matter while you're standing there.
      </p>

      <label
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragOver(false);
          handleFile(e.dataTransfer.files?.[0] ?? null);
        }}
        className={`mt-9 block cursor-pointer rounded-3xl p-8 md:p-12 text-center transition shadow-sm ${
          dragOver
            ? "border-2 border-poppy bg-poppy/5"
            : "border-2 border-dashed border-ink/20 bg-white hover:border-ink/40 hover:bg-stamp/40"
        }`}
      >
        <input
          ref={inputRef}
          type="file"
          accept="image/png,image/jpeg,image/webp"
          className="hidden"
          onChange={(e) => handleFile(e.target.files?.[0] ?? null)}
        />
        {preview ? (
          <div className="relative inline-block">
            <img src={preview} alt="Selected preview" className="max-h-96 rounded-2xl shadow-lg" />
            <button
              type="button"
              onClick={(e) => { e.preventDefault(); clear(); }}
              className="absolute -top-2.5 -right-2.5 bg-ink text-horizon rounded-full w-8 h-8 flex items-center justify-center shadow-md hover:bg-poppy transition-colors"
              aria-label="Clear image"
            >
              <X size={16} />
            </button>
            {status === "loading" && (
              <div className="absolute inset-0 overflow-hidden rounded-2xl pointer-events-none">
                <div className="absolute inset-x-0 h-1 scanline" style={{ background: "linear-gradient(90deg, transparent, var(--poppy), var(--marigold), transparent)" }} />
              </div>
            )}
          </div>
        ) : (
          <div className="flex flex-col items-center gap-3 py-6">
            <div className="w-16 h-16 rounded-2xl bg-ink text-horizon flex items-center justify-center shadow-lg">
              <Camera size={26} />
            </div>
            <div className="font-display text-xl">Drop a photo, or click to upload</div>
            <div className="label-mono">JPG, PNG or WebP · up to 10MB</div>
            <span className="btn-secondary mt-2 pointer-events-none">
              <Upload size={16} /> Choose file
            </span>
          </div>
        )}
      </label>

      <div className="mt-6 flex flex-wrap gap-3 items-center">
        <button className="btn-primary" disabled={!file || status === "loading"} onClick={identify}>
          {status === "loading" ? "Asking Gemini…" : "Identify landmark"}
        </button>
        {status === "loading" && <div className="label-mono">Reading the photo…</div>}
      </div>
      {error && <p className="mt-4 rounded-xl border border-poppy/30 bg-poppy/10 p-3.5 text-sm text-poppy">{error}</p>}

      {status === "done" && result && (
        <article className="ticket-card stamp-in mt-10 !p-0 overflow-hidden">
          <div className="bg-ink text-horizon px-6 md:px-8 py-7">
            <div className="flex items-start justify-between gap-4 flex-wrap">
              <div>
                <div className="label-mono !text-horizon/60">Identified</div>
                <h2 className="font-display italic text-4xl mt-1 !text-horizon">{result.name}</h2>
                <div className="mt-3 flex flex-wrap gap-4 text-sm text-horizon/75">
                  {(result.location || result.country) && (
                    <span className="inline-flex items-center gap-1.5">
                      <MapPin size={14} /> {[result.location, result.country].filter(Boolean).join(", ")}
                    </span>
                  )}
                  {result.architectureStyle && (
                    <span className="inline-flex items-center gap-1.5">
                      <Landmark size={14} /> {result.architectureStyle}
                    </span>
                  )}
                  {result.builtYear && (
                    <span className="inline-flex items-center gap-1.5">
                      <Clock3 size={14} /> {result.builtYear}
                    </span>
                  )}
                </div>
              </div>
              <div className="score-badge !w-16 !h-16">
                <div className="font-display text-lg">{result.confidence}%</div>
                <div className="text-[8px] tracking-widest opacity-70">SURE</div>
              </div>
            </div>
          </div>

          <div className="p-6 md:p-8 space-y-7">
            {result.summary && (
              <section>
                <div className="label-mono">Overview</div>
                <p className="mt-2 text-charcoal/80 leading-relaxed">{result.summary}</p>
              </section>
            )}

            {result.historicalBackground && (
              <section>
                <div className="label-mono">Historical background</div>
                <p className="mt-2 text-charcoal/80 leading-relaxed">{result.historicalBackground}</p>
              </section>
            )}

            {result.historicalFacts.length > 0 && (
              <section>
                <div className="label-mono">History highlights</div>
                <ul className="mt-3 space-y-2">
                  {result.historicalFacts.map((fact) => (
                    <li key={fact} className="flex gap-3 text-sm text-charcoal/80 leading-relaxed">
                      <Sparkles size={15} className="mt-0.5 shrink-0 text-marigold" />
                      <span>{fact}</span>
                    </li>
                  ))}
                </ul>
              </section>
            )}

            {result.whyItMatters && (
              <section className="rounded-2xl bg-stamp/60 border border-ink/8 p-4">
                <div className="label-mono">Why it matters</div>
                <p className="mt-2 text-sm text-charcoal/80 leading-relaxed">{result.whyItMatters}</p>
              </section>
            )}

            {(result.visitorTips.length > 0 || result.bestTimeToVisit) && (
              <section>
                <div className="label-mono">Visitor guide</div>
                {result.bestTimeToVisit && (
                  <p className="mt-2 text-sm text-charcoal/70">
                    Best time to visit: <span className="font-medium text-ink">{result.bestTimeToVisit}</span>
                  </p>
                )}
                <ul className="mt-3 space-y-2">
                  {result.visitorTips.map((tip) => (
                    <li key={tip} className="rounded-xl border border-ink/8 bg-white px-4 py-3 text-sm text-charcoal/80">
                      {tip}
                    </li>
                  ))}
                </ul>
              </section>
            )}

            {result.nearbyHighlights.length > 0 && (
              <section>
                <div className="label-mono">Nearby highlights</div>
                <div className="mt-3 flex flex-wrap gap-2">
                  {result.nearbyHighlights.map((place) => (
                    <span key={place} className="tag tag--sage">{place}</span>
                  ))}
                </div>
              </section>
            )}

            <div>
              {!feedbackOpen ? (
                <button className="text-sm underline decoration-poppy decoration-2 underline-offset-4 text-ink" onClick={() => setFeedbackOpen(true)}>
                  Not quite right?
                </button>
              ) : (
                <div className="flex gap-2 mt-2">
                  <input placeholder="What is it actually?" className="input-field flex-1" />
                  <button className="btn-secondary" onClick={() => setFeedbackOpen(false)}>Send</button>
                </div>
              )}
            </div>
          </div>
        </article>
      )}

      {status === "low" && (
        <article className="ticket-card mt-10 stamp-in">
          <div className="label-mono">Not confident enough</div>
          <h2 className="font-display text-2xl mt-2">We're not sure what this is</h2>
          <p className="mt-3 text-charcoal/75">
            Try a clearer or closer photo — a wider shot with more of the landmark's outline usually helps.
          </p>
          {result?.summary && <p className="mt-3 text-sm text-charcoal/60">{result.summary}</p>}
          <button className="btn-secondary mt-5" onClick={clear}>Try another photo</button>
        </article>
      )}
    </div>
  );
}
