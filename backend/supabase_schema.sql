-- Fielder data layer — run this in the Supabase SQL editor when (re)initializing.
--
-- Two tables:
--   businesses : maps an authenticated owner (auth.users) -> their business slug.
--   leads      : inbound leads + the AI triage result, keyed by slug.
--
-- Security model (Row Level Security):
--   * Anyone (anon) may INSERT a lead  — biz.html is a public page, the visitor
--     submitting is not logged in. They can never read anyone's leads.
--   * An owner may SELECT/UPDATE only leads whose slug they own in `businesses`.
--   * Owners fully own their own `businesses` rows.
--
-- The owner-only writes (intake persistence) come from the public page via the
-- anon key + these policies — no service_role key is exposed anywhere.

-- ── businesses ───────────────────────────────────────────────────────────────
create table if not exists public.businesses (
  id            uuid primary key default gen_random_uuid(),
  owner_id      uuid not null default auth.uid() references auth.users (id) on delete cascade,
  slug          text not null unique,          -- one business == one slug
  business_name text,
  flow          text,
  created_at    timestamptz not null default now()
);

alter table public.businesses enable row level security;

drop policy if exists "owner reads own businesses"   on public.businesses;
drop policy if exists "owner inserts own businesses"  on public.businesses;
drop policy if exists "owner updates own businesses"  on public.businesses;
drop policy if exists "owner deletes own businesses"  on public.businesses;

create policy "owner reads own businesses"
  on public.businesses for select
  to authenticated using (owner_id = auth.uid());

create policy "owner inserts own businesses"
  on public.businesses for insert
  to authenticated with check (owner_id = auth.uid());

create policy "owner updates own businesses"
  on public.businesses for update
  to authenticated using (owner_id = auth.uid()) with check (owner_id = auth.uid());

create policy "owner deletes own businesses"
  on public.businesses for delete
  to authenticated using (owner_id = auth.uid());

-- ── sites ────────────────────────────────────────────────────────────────────
-- The PUBLIC, published business page config. Separate from `businesses` so the
-- public page (anon) can read a config without ever seeing owner_id / private rows.
create table if not exists public.sites (
  slug       text primary key,
  config     jsonb not null,           -- the full BusinessConfig that biz.html renders
  updated_at timestamptz not null default now()
);

alter table public.sites enable row level security;

drop policy if exists "anyone can read a published site" on public.sites;
drop policy if exists "owner publishes own site"          on public.sites;
drop policy if exists "owner updates own site"            on public.sites;

-- Public pages: anyone may read.
create policy "anyone can read a published site"
  on public.sites for select
  to anon, authenticated using (true);

-- Only the owner of the slug (per `businesses`) may publish/update it.
create policy "owner publishes own site"
  on public.sites for insert
  to authenticated with check (
    slug in (select slug from public.businesses where owner_id = auth.uid())
  );

create policy "owner updates own site"
  on public.sites for update
  to authenticated using (
    slug in (select slug from public.businesses where owner_id = auth.uid())
  ) with check (
    slug in (select slug from public.businesses where owner_id = auth.uid())
  );

-- ── leads ────────────────────────────────────────────────────────────────────
create table if not exists public.leads (
  id           uuid primary key default gen_random_uuid(),
  slug         text not null,                  -- the business this lead came in for
  lead_name    text,
  lead_contact text,
  channel      text,                           -- website / instagram / google / facebook / text / referral
  message      text not null,                  -- the raw submission
  triage       jsonb,                          -- the full IntakeResult from /api/intake
  status       text not null default 'new'
                 check (status in ('new', 'approved', 'dismissed')),
  created_at   timestamptz not null default now()
);

create index if not exists leads_slug_created_idx on public.leads (slug, created_at desc);

alter table public.leads enable row level security;

drop policy if exists "anyone can submit a lead"   on public.leads;
drop policy if exists "owner reads slug leads"      on public.leads;
drop policy if exists "owner updates slug leads"    on public.leads;

-- Public intake: a visitor (anon) or a logged-in user may create a lead.
create policy "anyone can submit a lead"
  on public.leads for insert
  to anon, authenticated with check (true);

-- An owner can read only leads for slugs they own.
create policy "owner reads slug leads"
  on public.leads for select
  to authenticated using (
    slug in (select slug from public.businesses where owner_id = auth.uid())
  );

-- An owner can update (approve / dismiss) only their own slugs' leads.
create policy "owner updates slug leads"
  on public.leads for update
  to authenticated using (
    slug in (select slug from public.businesses where owner_id = auth.uid())
  ) with check (
    slug in (select slug from public.businesses where owner_id = auth.uid())
  );
