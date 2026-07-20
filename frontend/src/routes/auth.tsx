import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { ArrowLeft, KeyRound, MailCheck, RefreshCw, ShieldCheck } from "lucide-react";
import { useEffect, useState, type FormEvent } from "react";

import { useAuth } from "../lib/auth";

export const Route = createFileRoute("/auth")({
  component: AuthPage,
  head: () => ({ meta: [{ title: "Sign in — StoryMiles" }] }),
});

type AuthMode = "login" | "register" | "verify" | "forgot" | "reset";

function AuthPage() {
  const navigate = useNavigate();
  const { forgotPassword, login, register, resendVerification, resetPassword, verifyEmail } = useAuth();
  const [mode, setMode] = useState<AuthMode>("login");
  const [firstName, setFirstName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [code, setCode] = useState("");
  const [resendIn, setResendIn] = useState(0);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    if (resendIn <= 0) return;
    const timer = window.setInterval(() => setResendIn((value) => Math.max(0, value - 1)), 1000);
    return () => window.clearInterval(timer);
  }, [resendIn]);

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
      if (mode === "register") {
        await register(email, password, firstName);
        setCode("");
        setMode("verify");
        setResendIn(60);
        setSuccess("We sent a verification code to your inbox.");
        return;
      }
      if (mode === "forgot") {
        await forgotPassword(email);
        setCode("");
        setPassword("");
        setConfirmPassword("");
        setMode("reset");
        setResendIn(60);
        setSuccess("If that account exists, a reset code is on its way.");
        return;
      }
      if (mode === "reset") {
        if (password !== confirmPassword) {
          setError("Passwords do not match");
          return;
        }
        await resetPassword(email, code, password);
        setMode("login");
        setCode("");
        setPassword("");
        setConfirmPassword("");
        setSuccess("Password updated. Sign in with your new password.");
        return;
      }
      await verifyEmail(email, code);
      setMode("login");
      setCode("");
      setPassword("");
      setFirstName("");
      setSuccess("Email verified. Sign in to start exploring.");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Unable to continue");
    } finally {
      setSubmitting(false);
    }
  };

  const resend = async () => {
    if (resendIn > 0 || submitting) return;
    setSubmitting(true);
    setError("");
    setSuccess("");
    try {
      if (mode === "reset") await forgotPassword(email);
      else await resendVerification(email);
      setResendIn(60);
      setSuccess("A fresh code is on its way.");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Unable to resend the code");
    } finally {
      setSubmitting(false);
    }
  };

  const heading = {
    login: "Sign in to continue",
    register: "Create an account",
    verify: "Check your inbox",
    forgot: "Forgot your password?",
    reset: "Choose a new password",
  }[mode];

  const eyebrow = {
    login: "Welcome back",
    register: "Your travel profile",
    verify: "Email verification",
    forgot: "Account recovery",
    reset: "Secure reset",
  }[mode];

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
        {(mode === "verify" || mode === "forgot" || mode === "reset") && (
          <div className="mb-6 flex h-14 w-14 items-center justify-center rounded-2xl bg-sage/15 text-[#506752]">
            {mode === "verify" ? <MailCheck size={28} strokeWidth={1.8} /> : <KeyRound size={28} strokeWidth={1.8} />}
          </div>
        )}
        <div className="eyebrow">{eyebrow}</div>
        <h1 className="mt-3 font-display text-3xl italic md:text-4xl">{heading}</h1>
        <p className="mt-3 text-sm leading-relaxed text-charcoal/70">
          {mode === "verify" || mode === "reset" ? (
            <>
              We sent a 6-digit code to <strong className="text-ink">{email}</strong>.{" "}
              {mode === "verify"
                ? "Enter it below to confirm this email belongs to you."
                : "Enter it below to choose a new password."}
            </>
          ) : mode === "forgot" ? (
            "Enter your verified email and we’ll send a secure reset code."
          ) : (
            "Your recommendations and itineraries are saved securely to your verified account."
          )}
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

          {(mode === "login" || mode === "register" || mode === "forgot") && (
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
                autoFocus={mode === "forgot"}
              />
            </label>
          )}

          {(mode === "login" || mode === "register") && (
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
          )}

          {(mode === "verify" || mode === "reset") && (
            <label className="block">
              <span className="label-mono">{mode === "reset" ? "Reset code" : "Verification code"}</span>
              <input
                type="text"
                required
                inputMode="numeric"
                pattern="[0-9]{6}"
                maxLength={6}
                value={code}
                onChange={(event) => setCode(event.target.value.replace(/\D/g, "").slice(0, 6))}
                className="input-field mt-2 !py-4 text-center font-mono text-2xl font-semibold tracking-[0.5em]"
                autoComplete="one-time-code"
                placeholder="000000"
                autoFocus
              />
              <span className="mt-2 flex items-center gap-1.5 text-xs text-charcoal/55">
                <ShieldCheck size={14} /> Code expires in 10 minutes
              </span>
            </label>
          )}

          {mode === "reset" && (
            <>
              <label className="block">
                <span className="label-mono">New password</span>
                <input
                  type="password"
                  required
                  minLength={8}
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  className="input-field mt-1.5"
                  autoComplete="new-password"
                  placeholder="At least 8 characters"
                />
              </label>
              <label className="block">
                <span className="label-mono">Confirm password</span>
                <input
                  type="password"
                  required
                  minLength={8}
                  value={confirmPassword}
                  onChange={(event) => setConfirmPassword(event.target.value)}
                  className="input-field mt-1.5"
                  autoComplete="new-password"
                  placeholder="Repeat your new password"
                />
              </label>
            </>
          )}

          {success && (
            <p className="rounded-xl border border-sage/40 bg-sage/10 p-3.5 text-sm text-[#3f5240]">{success}</p>
          )}
          {error && <p className="rounded-xl border border-poppy/30 bg-poppy/10 p-3.5 text-sm text-poppy">{error}</p>}

          <button className="btn-primary w-full justify-center" disabled={submitting}>
            {submitting
              ? "Please wait…"
              : mode === "login"
                ? "Sign in"
                : mode === "register"
                  ? "Create account"
                  : mode === "verify"
                    ? "Verify email"
                    : mode === "forgot"
                      ? "Send reset code"
                      : "Reset password"}
          </button>
        </form>

        {mode === "login" && (
          <button
            type="button"
            className="mt-4 w-full text-sm text-charcoal/65 transition-colors hover:text-ink"
            onClick={() => {
              setMode("forgot");
              setError("");
              setSuccess("");
              setPassword("");
              setConfirmPassword("");
              setCode("");
            }}
          >
            Forgot password?
          </button>
        )}

        {mode === "verify" || mode === "reset" ? (
          <div className="mt-6 space-y-3 text-center text-sm">
            <button
              type="button"
              className="inline-flex items-center gap-2 text-charcoal/70 transition-colors hover:text-ink disabled:cursor-not-allowed disabled:opacity-50"
              disabled={resendIn > 0 || submitting}
              onClick={resend}
            >
              <RefreshCw size={15} />
              {resendIn > 0 ? `Send another code in ${resendIn}s` : "Send another code"}
            </button>
            <button
              type="button"
              className="flex w-full items-center justify-center gap-2 text-charcoal/60 transition-colors hover:text-ink"
              onClick={() => {
                setMode(mode === "reset" ? "forgot" : "register");
                setCode("");
                setError("");
                setSuccess("");
              }}
            >
              <ArrowLeft size={15} /> Change email
            </button>
          </div>
        ) : mode === "forgot" ? (
          <button
            type="button"
            className="mt-6 flex w-full items-center justify-center gap-2 text-sm text-charcoal/70 transition-colors hover:text-ink"
            onClick={() => {
              setMode("login");
              setError("");
              setSuccess("");
            }}
          >
            <ArrowLeft size={15} /> Back to sign in
          </button>
        ) : (
          <button
            type="button"
            className="mt-6 w-full text-sm text-charcoal/70 underline decoration-poppy decoration-2 underline-offset-4 transition-colors hover:text-ink"
            onClick={() => {
              setMode(mode === "login" ? "register" : "login");
              setError("");
              setSuccess("");
              setPassword("");
              setConfirmPassword("");
              if (mode === "login") setFirstName("");
            }}
          >
            {mode === "login" ? "New here? Create an account" : "Already have an account? Sign in"}
          </button>
        )}
      </div>
    </div>
  );
}
