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
