import { Link, useRouterState } from "@tanstack/react-router";
import { useState } from "react";
import { Menu, X, Compass, Map, Camera, Plane, LogOut, User, LayoutDashboard, Images } from "lucide-react";
import { useAuth } from "../lib/auth";

const links = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/recommendations", label: "Recommendations", icon: Compass },
  { to: "/plan", label: "Plan", icon: Map },
  { to: "/albums", label: "Albums", icon: Images },
  { to: "/scanner", label: "Scanner", icon: Camera },
] as const;

export function Nav() {
  const [open, setOpen] = useState(false);
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  const { user, logout } = useAuth();

  return (
    <>
      <header className="sticky top-0 z-40 glass-nav">
        <div className="mx-auto max-w-6xl px-5 h-16 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2 group">
            <span className="w-8 h-8 rounded-xl bg-ink text-horizon flex items-center justify-center transition-transform group-hover:-rotate-12">
              <Plane size={16} />
            </span>
            <span className="text-xl italic font-display text-ink tracking-tight font-semibold">
              StoryMiles
            </span>
          </Link>
          <nav className="hidden md:flex items-center gap-1">
            {links.map((l) => {
              const active = pathname.startsWith(l.to.split("/").slice(0, 2).join("/"));
              return (
                <Link
                  key={l.to}
                  to={l.to}
                  className={`px-3.5 py-2 text-sm font-medium rounded-full transition-colors ${
                    active
                      ? "text-ink bg-ink/8"
                      : "text-charcoal/70 hover:text-ink hover:bg-ink/5"
                  }`}
                >
                  {l.label}
                </Link>
              );
            })}
            <div className="w-px h-5 bg-ink/10 mx-2" />
            {user ? (
              <button className="btn-ghost text-sm" onClick={logout}>
                <LogOut size={15} /> Sign out
              </button>
            ) : (
              <Link to="/auth" className="btn-ghost text-sm">
                <User size={15} /> Sign in
              </Link>
            )}
            <Link to="/plan" className="btn-primary ml-2 !py-2.5 !px-5 text-sm">
              Start planning
            </Link>
          </nav>
          <button
            className="md:hidden btn-ghost"
            onClick={() => setOpen((v) => !v)}
            aria-label="Toggle menu"
          >
            {open ? <X size={22} /> : <Menu size={22} />}
          </button>
        </div>
        {open && (
          <div className="md:hidden border-t border-ink/10 bg-horizon">
            <div className="px-5 py-4 flex flex-col gap-1">
              {links.map((l) => (
                <Link
                  key={l.to}
                  to={l.to}
                  onClick={() => setOpen(false)}
                  className="py-2.5 px-3 rounded-xl text-ink font-medium hover:bg-ink/5"
                >
                  {l.label}
                </Link>
              ))}
              <Link to="/plan" onClick={() => setOpen(false)} className="btn-primary mt-3">
                Start planning
              </Link>
              {user ? (
                <button
                  className="btn-ghost mt-1 justify-start"
                  onClick={() => { logout(); setOpen(false); }}
                >
                  <LogOut size={15} /> Sign out
                </button>
              ) : (
                <Link to="/auth" onClick={() => setOpen(false)} className="btn-secondary mt-1">
                  Sign in
                </Link>
              )}
            </div>
          </div>
        )}
      </header>

      {/* Mobile bottom tab bar */}
      <nav className="md:hidden fixed bottom-0 inset-x-0 z-40 glass-nav !border-t !border-b-0">
        <div className="grid grid-cols-5">
          {links.map((l) => {
            const Icon = l.icon;
            const active = pathname.startsWith(l.to.split("/").slice(0, 2).join("/"));
            return (
              <Link
                key={l.to}
                to={l.to}
                className={`flex flex-col items-center gap-1 py-2.5 text-[10px] font-medium ${
                  active ? "text-poppy" : "text-charcoal/60"
                }`}
              >
                <Icon size={18} />
                <span className="truncate max-w-full px-0.5">{l.label}</span>
              </Link>
            );
          })}
        </div>
      </nav>
    </>
  );
}

export function Footer() {
  return (
    <footer className="mt-28 bg-ink text-horizon">
      <div className="mx-auto max-w-6xl px-5 py-16 grid md:grid-cols-4 gap-10">
        <div>
          <div className="flex items-center gap-2">
            <span className="w-8 h-8 rounded-xl bg-horizon/10 flex items-center justify-center">
              <Plane size={15} />
            </span>
            <span className="text-2xl italic font-display font-semibold !text-horizon">StoryMiles</span>
          </div>
          <p className="mt-4 text-sm opacity-60 leading-relaxed max-w-[220px]">
            Trips written before you pack a bag. Your calm AI travel companion.
          </p>
        </div>
        <FooterCol title="Product" items={["Recommendations", "Itinerary", "Scanner"]} />
        <FooterCol title="Company" items={["About", "Journal", "Contact"]} />
        <FooterCol title="Legal" items={["Privacy", "Terms", "Cookies"]} />
      </div>
      <div className="border-t border-horizon/10">
        <div className="mx-auto max-w-6xl px-5 py-6 flex items-center justify-between">
          <span className="text-xs opacity-50 label-mono !text-horizon/50">
            © {new Date().getFullYear()} StoryMiles
          </span>
          <span className="text-xs opacity-50 label-mono !text-horizon/50">
            Made for the road
          </span>
        </div>
      </div>
    </footer>
  );
}

function FooterCol({ title, items }: { title: string; items: string[] }) {
  return (
    <div>
      <div className="label-mono !text-horizon/50">{title}</div>
      <ul className="mt-4 space-y-2.5 text-sm">
        {items.map((i) => (
          <li key={i}>
            <a href="#" className="opacity-75 hover:opacity-100 hover:text-marigold transition">
              {i}
            </a>
          </li>
        ))}
      </ul>
    </div>
  );
}
