// Fielder client config (loaded by dashboard.html + onboarding.html).
//
// The Supabase ANON key is PUBLIC-safe to ship in a static page — Row Level
// Security protects your data, and this key only grants what your RLS policies
// allow. Do NOT put the service_role key here.
//
// Fill these in to turn on:
//   • real owner auth on the dashboard (Supabase Auth, email + password)
//   • portfolio image uploads in onboarding (Supabase Storage)
// Leave them blank to run in demo mode (placeholder login; paste-URL portfolio).
//
// Setup: create a project at supabase.com → Settings → API for the URL + anon
// key; enable Email auth; create a PUBLIC Storage bucket named "portfolios".
//   • lead intake (biz.html → AI triage) when BACKEND_URL points at the running
//     `backend/` service (the FastAPI app with your ANTHROPIC_API_KEY). Leave it
//     blank and biz.html falls back to the email-only contact form.
window.FIELDER = {
  SUPABASE_URL: "",
  SUPABASE_ANON_KEY: "",
  STORAGE_BUCKET: "portfolios",
  BACKEND_URL: "",          // e.g. "http://localhost:8000" or your deployed extractor URL
};
