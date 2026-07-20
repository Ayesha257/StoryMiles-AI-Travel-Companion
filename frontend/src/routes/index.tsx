import { createFileRoute, Link } from "@tanstack/react-router";
import { Compass, Map, Camera, ArrowRight, Sparkles } from "lucide-react";
import { useReveal } from "@/lib/hooks";

export const Route = createFileRoute("/")({
  component: Landing,
  head: () => ({
    meta: [
      { title: "StoryMiles — Your next trip, written before you pack" },
      { name: "description", content: "Personal destination matches, day-by-day itineraries, and landmark recognition — a calm travel companion." },
    ],
  }),
});

const steps = [
  { n: "01", Icon: Compass, title: "Tell us your style", body: "Budget, weather, the things you love doing. Four short questions, then we match you." },
  { n: "02", Icon: Sparkles, title: "Get matched destinations", body: "A handful of places that actually fit — ranked by a model trained on real city data." },
  { n: "03", Icon: Map, title: "Get a day-by-day plan", body: "Morning, afternoon, evening. Editable. Regenerate any day you don't love." },
];

const destinations = [
  { name: "Lisbon", country: "Portugal", tags: [["Food", "poppy"], ["Coastal", "sage"]], budget: "€€", img: "https://images.unsplash.com/photo-1555881400-74d7acaacd8b?w=800&q=80", blurb: "Tiled facades, custard tarts, and yellow trams climbing the hills." },
  { name: "Kyoto", country: "Japan", tags: [["History", "marigold"], ["Nature", "sage"]], budget: "€€€", img: "https://images.unsplash.com/photo-1493976040374-85c8e12f0c0e?w=800&q=80", blurb: "Temple gardens, quiet mornings by the river, tea when the light softens." },
  { name: "Marrakech", country: "Morocco", tags: [["Culture", "marigold"], ["Food", "poppy"]], budget: "€€", img: "https://images.unsplash.com/photo-1597212618440-806262de4f6b?w=800&q=80", blurb: "A city that hums — spice markets, riads, and rooftops at golden hour." },
  { name: "Reykjavík", country: "Iceland", tags: [["Nature", "sage"], ["Adventure", "poppy"]], budget: "€€€", img: "https://images.unsplash.com/photo-1531168556467-80aace0d0144?w=800&q=80", blurb: "Steam, lava fields, and low light that turns the whole island into a poster." },
  { name: "Oaxaca", country: "Mexico", tags: [["Food", "poppy"], ["Culture", "marigold"]], budget: "€", img: "https://images.unsplash.com/photo-1585975754487-53b6c72d3d90?w=800&q=80", blurb: "Markets, mezcal, and the best mole you'll eat this year." },
];

function Landing() {
  return (
    <div>
      <Hero />
      <HowItWorks />
      <SampleRow />
      <ScannerTeaser />
    </div>
  );
}

function Hero() {
  return (
    <section className="relative overflow-hidden">
      {/* soft radial background accent */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0"
        style={{
          background:
            "radial-gradient(900px 480px at 85% -10%, color-mix(in oklab, var(--marigold) 12%, transparent), transparent 65%), radial-gradient(700px 420px at -10% 110%, color-mix(in oklab, var(--sage) 10%, transparent), transparent 60%)",
        }}
      />
      <div className="relative mx-auto max-w-6xl px-5 pt-16 pb-16 md:pt-24 md:pb-28 grid md:grid-cols-[1.05fr_0.95fr] gap-12 items-center">
        <div>
          <div className="eyebrow">AI travel companion</div>
          <h1 className="mt-4">
            Your next trip,{" "}
            <span className="italic text-poppy">written</span> before you pack a bag.
          </h1>
          <p className="mt-6 text-base md:text-lg text-charcoal/75 max-w-lg leading-relaxed">
            StoryMiles matches you with places that fit, writes the days out
            end-to-end, and knows the landmark in your photo. Calm planning, then go.
          </p>
          <div className="mt-9 flex flex-wrap gap-3">
            <Link to="/plan" className="btn-primary">
              Plan my trip <ArrowRight size={16} />
            </Link>
            <Link to="/scanner" className="btn-secondary">
              <Camera size={16} /> Try the scanner
            </Link>
          </div>
          <div className="mt-10 flex items-center gap-7">
            <span className="stat-chip">559 destinations</span>
            <span className="stat-chip">Model-ranked matches</span>
            <span className="stat-chip hidden sm:inline-flex">AI itineraries</span>
          </div>
        </div>
        <HeroCollage />
      </div>
    </section>
  );
}

function HeroCollage() {
  return (
    <div className="relative hidden md:block" aria-hidden>
      <div className="grid grid-cols-2 gap-4">
        <div className="hero-media aspect-[3/4] mt-10">
          <img
            src="https://images.unsplash.com/photo-1493976040374-85c8e12f0c0e?w=700&q=80"
            alt=""
            className="w-full h-full object-cover"
            loading="eager"
          />
          <div className="absolute bottom-3 left-4 z-10 text-white font-display italic text-xl drop-shadow">Kyoto</div>
        </div>
        <div className="flex flex-col gap-4">
          <div className="hero-media aspect-[4/3]">
            <img
              src="https://images.unsplash.com/photo-1555881400-74d7acaacd8b?w=700&q=80"
              alt=""
              className="w-full h-full object-cover"
              loading="eager"
            />
            <div className="absolute bottom-3 left-4 z-10 text-white font-display italic text-xl drop-shadow">Lisbon</div>
          </div>
          <div className="hero-media aspect-[4/3] float-slow">
            <img
              src="https://images.unsplash.com/photo-1597212618440-806262de4f6b?w=700&q=80"
              alt=""
              className="w-full h-full object-cover"
              loading="eager"
            />
            <div className="absolute bottom-3 left-4 z-10 text-white font-display italic text-xl drop-shadow">Marrakech</div>
          </div>
        </div>
      </div>
    </div>
  );
}

function HowItWorks() {
  const ref = useReveal<HTMLDivElement>();
  return (
    <section className="section-band">
      <div ref={ref} className="reveal mx-auto max-w-6xl px-5 py-16 md:py-24">
        <div className="eyebrow">How it works</div>
        <h2 className="mt-3 font-display text-3xl md:text-4xl max-w-xl">
          Three steps. No airport-novel-length forms.
        </h2>
        <div className="mt-12 grid md:grid-cols-3 gap-6">
          {steps.map((s, i) => (
            <div
              key={s.n}
              className="ticket-card ticket-card--hoverable reveal is-visible"
              style={{ transitionDelay: `${i * 80}ms` }}
            >
              <div className="flex items-center justify-between">
                <div className="w-11 h-11 rounded-2xl bg-ink text-horizon flex items-center justify-center">
                  <s.Icon size={20} />
                </div>
                <span className="font-display text-4xl text-ink/10 font-semibold">{s.n}</span>
              </div>
              <h3 className="mt-5 font-display text-2xl">{s.title}</h3>
              <p className="mt-3 text-sm text-charcoal/70 leading-relaxed">{s.body}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function SampleRow() {
  const ref = useReveal<HTMLDivElement>();
  return (
    <section ref={ref} className="reveal mx-auto max-w-6xl px-5 py-16 md:py-24">
      <div className="flex items-end justify-between gap-6 mb-10">
        <div>
          <div className="eyebrow">A few places we love</div>
          <h2 className="mt-3 font-display text-3xl md:text-4xl">Sample destinations</h2>
        </div>
        <Link to="/recommendations" className="btn-ghost text-sm hidden md:inline-flex">
          See all matches <ArrowRight size={15} />
        </Link>
      </div>
      <div className="flex gap-6 overflow-x-auto pb-4 snap-x snap-mandatory -mx-5 px-5">
        {destinations.map((d) => (
          <article
            key={d.name}
            className="ticket-card ticket-card--hoverable !p-0 min-w-[280px] max-w-[300px] snap-start overflow-hidden"
          >
            <div className="card-img relative h-44">
              <img src={d.img} alt={d.name} className="w-full h-full object-cover" loading="lazy" />
              <div className="absolute top-3 right-3 label-mono !text-ink bg-white/90 backdrop-blur px-2.5 py-1 rounded-full shadow-sm">
                {d.budget}
              </div>
            </div>
            <div className="p-5">
              <div className="flex items-baseline justify-between gap-2">
                <div className="font-display italic text-2xl text-ink">{d.name}</div>
                <div className="text-xs text-charcoal/55 font-medium">{d.country}</div>
              </div>
              <p className="text-sm mt-2.5 text-charcoal/70 leading-relaxed">{d.blurb}</p>
              <div className="ticket-divider" />
              <div className="flex flex-wrap gap-1.5">
                {d.tags.map(([t, c]) => (
                  <span key={t} className={`tag tag--${c}`}>{t}</span>
                ))}
              </div>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

function ScannerTeaser() {
  const ref = useReveal<HTMLDivElement>();
  return (
    <section className="section-band">
      <div ref={ref} className="reveal mx-auto max-w-6xl px-5 py-16 md:py-24 grid md:grid-cols-2 gap-12 items-center">
        <div className="hero-media aspect-[16/11] order-last md:order-first">
          <img
            src="https://images.unsplash.com/photo-1431274172761-fca41d930114?w=900&q=80"
            alt="Traveler photographing a landmark"
            className="w-full h-full object-cover"
            loading="lazy"
          />
        </div>
        <div>
          <div className="eyebrow">Landmark scanner</div>
          <h2 className="mt-3 font-display text-3xl md:text-4xl max-w-md">
            Point your camera at anything old and impressive.
          </h2>
          <p className="mt-5 text-charcoal/70 max-w-md leading-relaxed">
            Upload a photo and StoryMiles identifies the landmark, tells you what
            it is, and shares a couple of things worth knowing while you're
            standing in front of it.
          </p>
          <Link to="/scanner" className="btn-primary mt-8">
            <Camera size={16} /> Scan a landmark
          </Link>
        </div>
      </div>
    </section>
  );
}
