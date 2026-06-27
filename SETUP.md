# Fielder — going live

The site at `wordups.github.io/Fielder/` renders today. The AI features (flyer
extract, lead triage, design directions, publish) stay dormant until you do the
three activation steps below. Nothing here needs code changes — just clicks +
filling `fielder-config.js`.

---

## 1. Supabase (the data layer)

1. Create a project at **supabase.com**.
2. **SQL Editor** → paste all of `backend/supabase_schema.sql` → **Run**.
   (Creates `businesses`, `leads`, `sites` with row-level security.)
3. **Authentication → Providers → Email**: enable it.
   - **Authentication → Sign In / Providers → Email → "Confirm email": turn OFF**
     for a frictionless demo (otherwise the first publish needs an email click).
4. **Storage** → New bucket named **`portfolios`** → make it **Public**
   (powers portfolio image uploads; paste-URL works without it).
5. **Project Settings → API**: copy the **Project URL** and the **anon public**
   key. (Never use the `service_role` key in the frontend.)

## 2. Backend (the AI service — needs your Anthropic key)

The backend can't live on GitHub Pages (Pages is static, and the API key can't
be in a public page). Deploy `backend/` anywhere that runs Docker:

**Render (simplest):**
1. render.com → **New → Blueprint** → pick this repo (it reads `render.yaml`).
2. Set **`ANTHROPIC_API_KEY`** in the dashboard (it's marked secret).
3. `FIELDER_ALLOWED_ORIGINS` is preset to `https://wordups.github.io`.
4. Deploy → copy the service URL, e.g. `https://fielder-backend.onrender.com`.
5. Verify: open `<that URL>/api/health` → should return `{"ok": true, ...}`.

> Railway / Fly.io work too — both build the `backend/Dockerfile`. Set the same
> two env vars (`ANTHROPIC_API_KEY`, `FIELDER_ALLOWED_ORIGINS`).

**Local test instead:** `cd backend && pip install -r requirements.txt && uvicorn app:app --port 8000`

## 3. Wire the frontend → commit → push

Fill `fielder-config.js` with the three values, then push (Pages redeploys):

```js
window.FIELDER = {
  SUPABASE_URL: "https://YOURPROJECT.supabase.co",
  SUPABASE_ANON_KEY: "eyJ...the anon public key...",
  STORAGE_BUCKET: "portfolios",
  BACKEND_URL: "https://fielder-backend.onrender.com",
};
```

```sh
git add fielder-config.js && git commit -m "Activate Fielder: Supabase + backend" && git push
```

---

## Verify the full loop

1. Home page → **Drop your flyer** → upload a poster/screenshot → lands in
   onboarding, prefilled.
2. **Pick a look** → Claude proposes 3 directions → click one.
3. **Publish** → sign in (new email = auto-creates account) → "Your site is
   fully live" with a `biz.html?slug=…` link.
4. Open that link → submit the intake form as a customer.
5. Open `dashboard.html`, sign in as the owner → the lead appears in **Leads**
   with an AI draft → **Approve & copy** / **Dismiss**.

## Notes / next
- A claimed-but-unpublished `?slug=` shows a **"Coming soon"** placeholder.
- Approve currently **copies the reply** for you to send. Automated send
  (email → SMS) needs an email/SMS provider (Resend/Twilio) — not wired yet.
- CORS is env-driven (`FIELDER_ALLOWED_ORIGINS`); keep it locked to your Pages
  origin in production, `*` only for local.
