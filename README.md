# Fielder

**A professional website plus a business hub for service providers — to manage leads, bookings, customers, capacity, ghosted opportunities, and follow-ups from one place.**

Fielder is for small service businesses that already have customers but run demand through too many scattered channels: Instagram DMs, texts, missed calls, Google Business, referrals, Facebook — and memory. Fielder gives the owner one front door for customers and one back office for themselves.

---

## The offer

Two things, one flat price:

1. **A public business site** — a clean, mobile-friendly page like `mikecuts.fielder.app` to drop in every bio, text, and Google profile. Customers view services, submit intake, book/request/reserve, and upload photos when a job needs it.
2. **A private owner dashboard** — every lead lands here and gets pushed toward the next action. The owner sees new leads, booked and confirmed customers, completed jobs, capacity remaining, great clients, at-risk clients, ghosted customers, and where the revenue opportunity is.

A lead should never submit a form and disappear. After intake, Fielder pushes them to the next step — book, reserve, request a quote, join a waitlist, or confirm.

---

## One engine, four flows

Fielder is **not** twenty industry-specific apps. It's one config-driven engine with four reusable flows. Labels change by industry; the engine stays the same.

| Flow | For | Pipeline |
|------|-----|----------|
| **Appointment** | Barbers, trainers, coaches, photographers, detailers | Lead → Book → Confirmed → Completed → Returning |
| **Quote** | Pressure washing, handyman, contractors, lawn, detailing | Lead → Review → Quote Sent → Accepted → Scheduled → Completed |
| **Capacity** | Meal prep, lawn routes, cleaning, batch services | Lead → Reserve Slot → Scheduled → Completed → Recurring |
| **Membership** | Monthly cleaning, monthly lawn, coaching programs | Lead → Subscribed → Active → Renewal → Retained |

Each flow surfaces its own dashboard metrics — e.g. Appointment tracks no-shows and capacity %, Quote tracks acceptance rate and ghosted quotes, Capacity tracks utilization and waitlist, Membership tracks churn and lifetime value.

### Config-driven by design

One codebase, many businesses. A client site is selected by business type:

```json
{ "businessName": "Mike's Cuts",    "slug": "mikecuts",    "industry": "barber",    "flow": "appointment" }
{ "businessName": "Fresh Plates",   "slug": "freshplates", "industry": "meal_prep", "flow": "capacity" }
{ "businessName": "Green Leaf Lawn","slug": "greenleaf",   "industry": "lawn_care", "flow": "capacity" }
```

---

## Who it's for

Barbers · lawn care · meal preppers · mobile car washers/detailers · cleaners · trainers · coaches · handymen · photographers · local service providers.

If customers already find you but you manage them in your head, Fielder is for you.

---

## Pricing direction

- **$75/month max** — flat, no per-lead charges.
- Launch offer may include **Month 2 free**.
- Optional bi-weekly payment later.
- Focus is **volume and low-touch onboarding**, not high-ticket custom work.
- Goal: a new client live in roughly **three minutes**.

---

## What's in this repo today

This repo currently holds the **public marketing / landing page** (`index.html`) — a single static file, no build step, safe to serve from GitHub Pages or any static host. It tells the Fielder product story: the problem, the offer, the four flows, an interactive owner-dashboard preview, a capacity demo, customer-health categories, and pricing.

```
Fielder/
├── index.html   # standalone landing page (the marketing front door)
└── README.md
```

> GitHub Pages is fine for this public preview/marketing page **only**. It is not the product runtime — the owner dashboard, auth, and storage are a separate build and are not part of this static page.

---

## Roadmap (not built here yet)

- Owner dashboard, auth, and persistent lead storage
- Intake → booking integration (Calendly or equivalent)
- Email notifications, then SMS after confirmation (confirmations, reminders, reactivation, ghost-recovery)
- Per-client onboarding that generates a configured site automatically

---

## Scope note

STALL is a **separate product** and is not part of Fielder. Fielder does not import or build over STALL.
