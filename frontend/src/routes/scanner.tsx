import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useRef, useState } from "react";
import { Camera, Clock3, Landmark, MapPin, Sparkles, Upload, X } from "lucide-react";
import { api, friendlyApiMessage } from "../lib/api";
import { useAuth } from "../lib/auth";
import {
  MAX_PHOTO_SIZE_MB,
  prepareImageForUpload,
  validateImageFile,
} from "../lib/imageUpload";

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
  const galleryInputRef = useRef<HTMLInputElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [status, setStatus] = useState<"idle" | "preparing" | "loading" | "done" | "low">("idle");
  const [result, setResult] = useState<Result | null>(null);
  const [feedbackOpen, setFeedbackOpen] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const [error, setError] = useState("");
  const [cameraOpen, setCameraOpen] = useState(false);
  const [cameraHint, setCameraHint] = useState("");
  const [cameraStarting, setCameraStarting] = useState(false);

  const stopCamera = () => {
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
    if (videoRef.current) videoRef.current.srcObject = null;
  };

  const closeCamera = () => {
    stopCamera();
    setCameraOpen(false);
    setCameraStarting(false);
  };

  useEffect(() => {
    return () => stopCamera();
  }, []);

  const handleFile = async (f: File | null) => {
    if (!f) return;
    setError("");
    setCameraHint("");
    const early = validateImageFile(f);
    if (early) {
      setError(early);
      return;
    }
    setStatus("preparing");
    try {
      const prepared = await prepareImageForUpload(f);
      if (preview) URL.revokeObjectURL(preview);
      setFile(prepared.file);
      setPreview(prepared.previewUrl);
      setStatus("idle");
      setResult(null);
    } catch (cause) {
      setStatus("idle");
      setError(cause instanceof Error ? cause.message : "Could not prepare this photo");
    }
  };

  const clear = () => {
    if (preview) URL.revokeObjectURL(preview);
    setFile(null);
    setPreview(null);
    setStatus("idle");
    setResult(null);
    setFeedbackOpen(false);
    setError("");
    setCameraHint("");
  };

  const openCamera = async () => {
    setCameraHint("");
    setError("");
    if (!navigator.mediaDevices?.getUserMedia) {
      setCameraHint("Live camera isn't supported in this browser. Use Upload Photo instead.");
      return;
    }
    setCameraOpen(true);
    setCameraStarting(true);
  };

  useEffect(() => {
    if (!cameraOpen) return;

    let cancelled = false;

    const start = async () => {
      try {
        let stream: MediaStream;
        try {
          stream = await navigator.mediaDevices.getUserMedia({
            audio: false,
            video: {
              facingMode: { ideal: "environment" },
              width: { ideal: 1920 },
              height: { ideal: 1080 },
            },
          });
        } catch {
          stream = await navigator.mediaDevices.getUserMedia({ audio: false, video: true });
        }
        if (cancelled) {
          stream.getTracks().forEach((track) => track.stop());
          return;
        }
        streamRef.current = stream;
        const video = videoRef.current;
        if (video) {
          video.srcObject = stream;
          await video.play();
        }
        setCameraStarting(false);
      } catch {
        if (!cancelled) {
          closeCamera();
          setCameraHint(
            "Camera permission was denied or no camera was found. Allow camera access, or use Upload Photo instead.",
          );
        }
      }
    };

    void start();
    return () => {
      cancelled = true;
    };
  }, [cameraOpen]);

  const captureLivePhoto = async () => {
    const video = videoRef.current;
    if (!video || !video.videoWidth) return;

    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.drawImage(video, 0, 0);

    const blob = await new Promise<Blob | null>((resolve) =>
      canvas.toBlob(resolve, "image/jpeg", 0.92),
    );
    if (!blob) {
      setCameraHint("Couldn't capture that frame — try again.");
      return;
    }

    const captured = new File([blob], `landmark-${Date.now()}.jpg`, {
      type: "image/jpeg",
      lastModified: Date.now(),
    });
    closeCamera();
    await handleFile(captured);
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
      setError(
        friendlyApiMessage(
          cause,
          "We couldn't identify this landmark. Try a clearer photo.",
        ),
      );
    }
  };

  return (
    <div className="mx-auto max-w-3xl px-5 py-12 md:py-20">
      <div className="eyebrow">Landmark scanner</div>
      <h1 className="mt-3 font-display text-4xl md:text-5xl">What are you looking at?</h1>
      <p className="mt-4 text-charcoal/75 max-w-lg leading-relaxed">
        Open your camera for a live shot, or upload a photo — Gemini identifies the landmark and
        shares history and visitor tips.
      </p>

      {/* Gallery upload only — Take Photo uses live getUserMedia, not a file picker */}
      <input
        ref={galleryInputRef}
        type="file"
        accept="image/png,image/jpeg,image/webp"
        className="hidden"
        onChange={(e) => {
          void handleFile(e.target.files?.[0] ?? null);
          e.target.value = "";
        }}
      />

      <div className="mt-8 flex flex-wrap gap-3">
        <button type="button" className="btn-primary" onClick={() => void openCamera()}>
          <Camera size={16} /> Take Photo
        </button>
        <button
          type="button"
          className="btn-secondary"
          onClick={() => galleryInputRef.current?.click()}
        >
          <Upload size={16} /> Upload Photo
        </button>
      </div>
      {cameraHint && (
        <p className="mt-3 text-sm text-charcoal/70 rounded-xl bg-ink/5 px-3 py-2">{cameraHint}</p>
      )}

      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragOver(false);
          void handleFile(e.dataTransfer.files?.[0] ?? null);
        }}
        className={`mt-6 rounded-3xl p-8 md:p-12 text-center transition shadow-sm ${
          dragOver
            ? "border-2 border-poppy bg-poppy/5"
            : "border-2 border-dashed border-ink/20 bg-white"
        }`}
      >
        {preview ? (
          <div className="relative inline-block">
            <img src={preview} alt="Selected preview" className="max-h-96 rounded-2xl shadow-lg" />
            <button
              type="button"
              onClick={clear}
              className="absolute -top-2.5 -right-2.5 bg-ink text-horizon rounded-full w-8 h-8 flex items-center justify-center shadow-md hover:bg-poppy transition-colors"
              aria-label="Clear image"
            >
              <X size={16} />
            </button>
            {(status === "loading" || status === "preparing") && (
              <div className="absolute inset-0 overflow-hidden rounded-2xl pointer-events-none bg-ink/20 flex items-end justify-center pb-4">
                <span className="label-mono !text-horizon bg-ink/70 px-3 py-1 rounded-full">
                  {status === "preparing" ? "Compressing…" : "Asking Gemini…"}
                </span>
              </div>
            )}
          </div>
        ) : (
          <div className="flex flex-col items-center gap-3 py-6">
            <div className="w-16 h-16 rounded-2xl bg-ink text-horizon flex items-center justify-center shadow-lg">
              <Camera size={26} />
            </div>
            <div className="font-display text-xl">Take a live photo or upload one</div>
            <div className="label-mono">
              JPG, PNG or WebP · up to {MAX_PHOTO_SIZE_MB}MB · auto-compressed
            </div>
          </div>
        )}
      </div>

      <div className="mt-6 flex flex-wrap gap-3 items-center">
        <button
          className="btn-primary"
          disabled={!file || status === "loading" || status === "preparing"}
          onClick={identify}
        >
          {status === "loading" ? "Asking Gemini…" : status === "preparing" ? "Preparing…" : "Identify landmark"}
        </button>
        {status === "loading" && <div className="label-mono">Reading the photo…</div>}
      </div>
      {error && (
        <div className="mt-4 ticket-card !p-4 border border-poppy/20">
          <div className="label-mono">Couldn't identify this</div>
          <p className="mt-2 text-sm text-charcoal/80">{error}</p>
          <p className="mt-2 text-xs text-charcoal/50">
            Try a clearer live shot, or use Upload Photo if the camera was blocked.
          </p>
        </div>
      )}

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
                <button
                  className="text-sm underline decoration-poppy decoration-2 underline-offset-4 text-ink"
                  onClick={() => setFeedbackOpen(true)}
                >
                  Not quite right?
                </button>
              ) : (
                <div className="flex gap-2 mt-2">
                  <input placeholder="What is it actually?" className="input-field flex-1" />
                  <button className="btn-secondary" onClick={() => setFeedbackOpen(false)}>
                    Send
                  </button>
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
          <button className="btn-secondary mt-5" onClick={clear}>
            Try another photo
          </button>
        </article>
      )}

      {cameraOpen && (
        <div
          className="fixed inset-0 z-50 bg-ink/80 backdrop-blur-sm flex items-center justify-center p-4"
          role="dialog"
          aria-modal="true"
          aria-label="Live camera"
        >
          <div className="w-full max-w-lg ticket-card !p-0 overflow-hidden">
            <div className="flex items-center justify-between px-5 py-4 border-b border-ink/8">
              <div>
                <div className="label-mono">Live camera</div>
                <p className="text-sm text-charcoal/70 mt-0.5">Frame the landmark, then capture</p>
              </div>
              <button type="button" className="btn-ghost !p-2" onClick={closeCamera} aria-label="Close camera">
                <X size={18} />
              </button>
            </div>
            <div className="relative bg-ink aspect-[3/4] sm:aspect-video">
              <video
                ref={videoRef}
                playsInline
                muted
                autoPlay
                className="absolute inset-0 h-full w-full object-cover"
              />
              {cameraStarting && (
                <div className="absolute inset-0 flex items-center justify-center text-horizon label-mono">
                  Starting camera…
                </div>
              )}
            </div>
            <div className="flex flex-wrap gap-3 justify-center p-5">
              <button
                type="button"
                className="btn-primary"
                disabled={cameraStarting}
                onClick={() => void captureLivePhoto()}
              >
                <Camera size={16} /> Capture photo
              </button>
              <button type="button" className="btn-secondary" onClick={closeCamera}>
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
