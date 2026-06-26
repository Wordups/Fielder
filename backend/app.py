"""Fielder onboarding extractor — PRIVATE backend.

Turns a small service business's existing material (a flyer/poster photo, an
Instagram-bio screenshot, or pasted text) into a structured Fielder BusinessConfig
using Claude vision + structured outputs. The static frontend (biz.html /
onboarding.html / dashboard.html) renders that config into a live business page
and owner dashboard.

This needs ANTHROPIC_API_KEY and therefore CANNOT run on GitHub Pages — Pages is
static. Run it locally or on a private host; the static pages call /api/extract.

Run:  uvicorn app:app --reload --port 8000   (from this backend/ dir)
"""

from __future__ import annotations

import base64
import json
import os
import re
from typing import Literal, Optional

import anthropic
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

MODEL = "claude-opus-4-8"


# ── The config contract the frontend renders (one schema, many businesses) ──
class Service(BaseModel):
    name: str
    price: Optional[str] = None
    description: Optional[str] = None


class Contact(BaseModel):
    email: Optional[str] = None
    phone: Optional[str] = None
    instagram: Optional[str] = None
    location: Optional[str] = None


class BusinessConfig(BaseModel):
    businessName: str
    slug: str
    industry: str
    flow: Literal["appointment", "quote", "capacity", "membership"]
    tagline: Optional[str] = None
    brandColor: Optional[str] = None
    about: Optional[str] = None
    contact: Contact = Field(default_factory=Contact)
    services: list[Service] = Field(default_factory=list)
    portfolio: list[str] = Field(default_factory=list)


# ── The intake contract: one inbound lead → classification + routing + draft reply ──
class IntakeResult(BaseModel):
    is_real_lead: bool
    is_spam: bool
    intent: str
    service_interest: Optional[str] = None
    urgency: Literal["high", "medium", "low"] = "medium"
    next_action: Literal[
        "book", "send_quote", "reserve_slot", "subscribe",
        "join_waitlist", "clarify", "decline_spam",
    ]
    draft_reply: str
    needs_owner_attention: bool = False
    summary: str


class IntakeRequest(BaseModel):
    config: BusinessConfig          # the business the lead came in for (drives the flow)
    message: str                    # the lead's free-text submission / DM / text
    lead_name: Optional[str] = None
    lead_contact: Optional[str] = None
    channel: Optional[str] = None   # instagram / google / facebook / text / referral / website


INTAKE_INSTRUCTIONS = """You are the intake agent for a small local service business on Fielder \
(a website-plus-dashboard hub for service providers). You receive ONE inbound lead — a website form \
submission, an Instagram/Facebook DM, a text, or a referral note — together with the business's \
profile and its Fielder flow. Classify the lead, route it to the next step in that flow, and draft a \
short reply the OWNER will review before anything is sent. You never send messages yourself.

Rules:
- is_spam: true for bots, sales pitches aimed at the owner, gibberish, or off-topic messages. \
If spam, set is_real_lead false and next_action "decline_spam".
- service_interest: match to one of the business's listed services if the lead names or implies one; otherwise null.
- urgency: high if they want something today/ASAP or name an event date soon; low for vague "just looking"; else medium.
- next_action: pick the step that fits the business's flow:
    appointment -> "book"        (or "clarify" if they haven't said what service or when)
    quote       -> "send_quote"  (or "clarify" if you can't estimate without more info)
    capacity    -> "reserve_slot" (or "join_waitlist" if they imply a full/known-busy period)
    membership  -> "subscribe"   (or "clarify")
  Use "clarify" whenever key info is missing. Never invent prices, availability, or dates.
- draft_reply: 1-3 sentences, warm and on-brand, written as the owner texting the lead back, moving them \
toward next_action. Don't promise specific times or prices you don't have — ask for them instead. Keep it SMS-length.
- needs_owner_attention: true for complaints, refunds, unusually large/complex jobs, or anything you're unsure how to handle.
- summary: one short line for the owner's dashboard (who + what they want)."""


# ── Design directions: a draft config in → a few distinct visual directions out ──
class DesignDirection(BaseModel):
    name: str            # short label for the look, e.g. "Bold & modern"
    vibe: str            # one line describing the aesthetic
    brandColor: str      # hex, e.g. "#c2410c"
    tagline: str
    about: str           # 1-2 sentences


class DesignDirections(BaseModel):
    directions: list[DesignDirection]


class DesignRequest(BaseModel):
    config: BusinessConfig


DESIGN_INSTRUCTIONS = """You are the brand designer for a small local service business being set up on \
Fielder. Given the business profile, propose exactly THREE genuinely distinct visual directions the owner \
can choose from for their public page.

Rules:
- Make the three directions clearly different from each other in mood and palette (e.g. one bold/modern, \
one warm/classic, one clean/minimal) — do NOT return three variations of the same look, and do not default \
to generic green.
- brandColor: a hex color that anchors each direction and genuinely fits this industry and vibe. Pick colors \
a real brand in this trade would use; avoid the same hue across directions.
- tagline: short and specific to THIS business (use its name/services), not a generic slogan.
- about: 1-2 warm sentences in the business's voice.
- name + vibe: keep them short so the owner can skim and pick."""


EXTRACT_INSTRUCTIONS = """You are onboarding a small local service business onto Fielder \
(a website-plus-dashboard hub for service providers). Extract a structured business profile \
from the material provided — it may be a photo of a flyer/poster, a screenshot of an \
Instagram bio/profile, or pasted text.

Rules:
- slug: lowercase, url-safe (letters/numbers/hyphens), derived from the business name.
- flow: pick the Fielder workflow that best fits how they sell:
    appointment = time-slot bookings (barbers, trainers, coaches, photographers, detailers)
    quote       = estimate-then-schedule (pressure washing, handyman, contractors, lawn, detailing)
    capacity    = batch/route based (meal prep, lawn routes, cleaning, batch services)
    membership  = recurring/subscription (monthly cleaning/lawn, coaching programs)
- services: each offering you can see, with its price if one is shown. Don't invent prices.
- brandColor: a hex color (e.g. "#3da35d") that fits the business's vibe; default to a clean green if unclear.
- contact: only fill email / phone / instagram / location if actually present in the material.
- portfolio: only include image URLs if they are literally present as text; otherwise leave empty.
- Leave any unknown field null/empty. Never fabricate contact info, prices, or services."""


app = FastAPI(title="Fielder Onboarding Extractor", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # demo-open; tighten to your Pages origin in production
    allow_methods=["*"],
    allow_headers=["*"],
)

client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from the environment


@app.get("/api/health")
def health() -> dict:
    return {"ok": True, "model": MODEL, "key_configured": bool(os.environ.get("ANTHROPIC_API_KEY"))}


@app.post("/api/extract")
async def extract(
    image: Optional[UploadFile] = File(default=None),
    text: str = Form(default=""),
) -> dict:
    """Image and/or pasted text in → BusinessConfig JSON out."""
    text = (text or "").strip()
    blocks: list[dict] = []

    if image is not None:
        raw = await image.read()
        if len(raw) > 8 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="Image too large (max 8MB)")
        blocks.append(
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": image.content_type or "image/png",
                    "data": base64.standard_b64encode(raw).decode("utf-8"),
                },
            }
        )

    if not image and not text:
        raise HTTPException(status_code=400, detail="Provide an image or some text to extract from.")

    prompt = EXTRACT_INSTRUCTIONS
    if text:
        prompt += f"\n\nPasted text / bio:\n{text}"
    blocks.append({"type": "text", "text": prompt})

    try:
        response = client.messages.parse(
            model=MODEL,
            max_tokens=2000,
            messages=[{"role": "user", "content": blocks}],
            output_format=BusinessConfig,
        )
    except anthropic.APIError as exc:  # surfaces auth/rate/overload cleanly
        raise HTTPException(status_code=502, detail=f"Extraction failed: {exc}") from exc

    config = response.parsed_output
    if config is None:
        raise HTTPException(status_code=502, detail="Could not extract a business profile from that.")

    # Normalize the slug defensively (the model is good, but enforce the contract).
    config.slug = re.sub(r"[^a-z0-9]+", "-", (config.slug or config.businessName).lower()).strip("-")
    return config.model_dump()


@app.post("/api/intake")
async def intake(req: IntakeRequest) -> dict:
    """One inbound lead + business config in -> a routed, drafted IntakeResult out.

    Stateless triage: classify -> route to the business's flow -> draft a reply.
    The draft is returned for OWNER REVIEW; nothing is sent here. Persistence
    (a leads table) and the dashboard approval queue are the next steps.
    """
    message = (req.message or "").strip()
    if not message:
        raise HTTPException(status_code=400, detail="Provide the lead's message to triage.")

    prompt = (
        INTAKE_INSTRUCTIONS
        + "\n\nBusiness profile (JSON):\n"
        + json.dumps(req.config.model_dump(), ensure_ascii=False)
        + "\n\nInbound lead:"
        + f"\n- channel: {req.channel or 'unknown'}"
        + f"\n- name: {req.lead_name or 'unknown'}"
        + f"\n- contact: {req.lead_contact or 'unknown'}"
        + f"\n- message: {message}"
    )

    try:
        response = client.messages.parse(
            model=MODEL,
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}],
            output_format=IntakeResult,
        )
    except anthropic.APIError as exc:  # surfaces auth/rate/overload cleanly
        raise HTTPException(status_code=502, detail=f"Intake triage failed: {exc}") from exc

    result = response.parsed_output
    if result is None:
        raise HTTPException(status_code=502, detail="Could not triage that lead.")
    return result.model_dump()


@app.post("/api/design")
async def design(req: DesignRequest) -> dict:
    """A draft BusinessConfig in -> three distinct visual directions to choose from."""
    prompt = (
        DESIGN_INSTRUCTIONS
        + "\n\nBusiness profile (JSON):\n"
        + json.dumps(req.config.model_dump(), ensure_ascii=False)
    )
    try:
        response = client.messages.parse(
            model=MODEL,
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}],
            output_format=DesignDirections,
        )
    except anthropic.APIError as exc:  # surfaces auth/rate/overload cleanly
        raise HTTPException(status_code=502, detail=f"Design generation failed: {exc}") from exc

    result = response.parsed_output
    if result is None:
        raise HTTPException(status_code=502, detail="Could not generate design directions.")
    return result.model_dump()
