import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useState, type FormEvent } from "react";

import { useAuth } from "../lib/auth";

export const Route = createFileRoute("/auth")({
  component: AuthPage,
  head: () => ({ meta: [{ title: "Sign in — StoryMiles" }] }),
});

function AuthPage() {
  const navigate = useNavigate();
  const { login, register } = useAuth();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [firstName, setFirstName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setSubmitting(true);
    setError("");
    setSuccess("");
    try {
      if (mode === "login") {
        await login(email, password);
        await navigate({ to: "/dashboard" });
        return;
      }
      await register(email, password, firstName);
      setMode("login");
      setPassword("");
      setFirstName("");
      setSuccess("Account created. Sign in to continue.");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Unable to sign in");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="relative mx-auto max-w-md px-5 py-16 md:py-24">
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 -z-10"
        style={{
          background:
            "radial-gradient(600px 400px at 50% 0%, color-mix(in oklab, var(--marigold) 10%, transparent), transparent 70%)",
        }}
      />
      <div className="ticket-card !p-8 md:!p-10">
        <div className="eyebrow">{mode === "login" ? "Welcome back" : "Your travel profile"}</div>
        <h1 className="mt-3 font-display text-3xl md:text-4xl italic">
          {mode === "login" ? "Sign in to continue" : "Create an account"}
        </h1>
        <p className="mt-3 text-sm text-charcoal/70 leading-relaxed">
          Your recommendations and itineraries are saved securely to your account.
        </p>

        <form className="mt-8 space-y-5" onSubmit={submit} autoComplete="off">
          {mode === "register" && (
            <label className="block">
              <span className="label-mono">First name</span>
              <input
                value={firstName}
                onChange={(event) => setFirstName(event.target.value)}
                className="input-field mt-1.5"
                autoComplete="off"
                placeholder="Your first name"
              />
            </label>
          )}
          <label className="block">
            <span className="label-mono">Email</span>
            <input
              type="email"
              required
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              className="input-field mt-1.5"
              autoComplete="off"
              placeholder="you@example.com"
            />
          </label>
          <label className="block">
            <span className="label-mono">Password</span>
            <input
              type="password"
              required
              minLength={8}
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              className="input-field mt-1.5"
              autoComplete="new-password"
              placeholder={mode === "login" ? "Your password" : "At least 8 characters"}
            />
          </label>

          {success && (
            <p className="rounded-xl border border-sage/40 bg-sage/10 p-3.5 text-sm text-[#3f5240]">
              {success}
            </p>
          )}
          {error && <p className="rounded-xl border border-poppy/30 bg-poppy/10 p-3.5 text-sm text-poppy">{error}</p>}

          <button className="btn-primary w-full justify-center" disabled={submitting}>
            {submitting ? "Connecting…" : mode === "login" ? "Sign in" : "Create account"}
          </button>
        </form>

        <button
          className="mt-6 w-full text-sm text-charcoal/70 hover:text-ink underline decoration-poppy decoration-2 underline-offset-4 transition-colors"
          onClick={() => {
            setMode(mode === "login" ? "register" : "login");
            setError("");
            setSuccess("");
            setPassword("");
            if (mode === "login") setFirstName("");
          }}
        >
          {mode === "login" ? "New here? Create an account" : "Already have an account? Sign in"}
        </button>
      </div>
    </div>
  );
}
