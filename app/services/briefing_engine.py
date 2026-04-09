from datetime import datetime, timezone
from typing import List

from app.models.schemas import BriefingItem, BriefingRequest, BriefingResponse
from app.services.renderers import render_html, render_text


def build_mock_items(req: BriefingRequest, generated_at: str) -> List[BriefingItem]:
    items: List[BriefingItem] = [
        BriefingItem(
            title="Studios continue concentrating spend into higher-conviction projects",
            source="Industry Synthesis",
            url="https://example.com/source-1",
            published=generated_at,
            summary="Major buyers continue emphasizing clearer audience positioning, fewer bets, and stronger packaging discipline.",
            investorWhy="Selective spend tends to favor projects with tighter risk control, clearer demand signals, and stronger distribution logic.",
            section="Investment / Deals"
        ),
        BriefingItem(
            title="International incentives remain a meaningful lever in production planning",
            source="Industry Synthesis",
            url="https://example.com/source-2",
            published=generated_at,
            summary="Territories outside the US continue competing on rebates, infrastructure, and production support.",
            investorWhy="Where a project is produced can materially affect its return profile, financing stack, and timing of cash recovery.",
            section="International"
        ),
        BriefingItem(
            title="Creator ecosystems continue competing for audience time and monetization",
            source="Industry Synthesis",
            url="https://example.com/source-3",
            published=generated_at,
            summary="Digital-first formats and creators continue drawing attention and ad budgets away from some traditional media channels.",
            investorWhy="Creator-native ecosystems increasingly matter as pipeline sources for IP, talent, and audience validation.",
            section="New Media / Creator Economy"
        )
    ]

    wanted = {c.lower() for c in req.categories}
    if not wanted:
        return items

    filtered: List[BriefingItem] = []
    for item in items:
        hay = f"{item.title} {item.section}".lower()
        if "film" in wanted and "investment" in hay:
            filtered.append(item)
            continue
        if "investment" in wanted and "investment" in hay:
            filtered.append(item)
            continue
        if "new_media" in wanted and "creator" in hay:
            filtered.append(item)
            continue
        if "incentives" in wanted and "international" in hay:
            filtered.append(item)
            continue
        if "tv" in wanted:
            filtered.append(item)
            continue

    return filtered or items


def generate_briefing_payload(req: BriefingRequest) -> BriefingResponse:
    generated_at = datetime.now(timezone.utc).isoformat()

    executive_summary = [
        "Capital remains selective and is rewarding projects with clearer commercial logic.",
        "International incentive strategy can materially improve financing efficiency and production economics.",
        "Creator-led ecosystems remain important as audience, talent, and intellectual property discovery channels."
    ]

    items = build_mock_items(req, generated_at)

    html = render_html(
        generated_at=generated_at,
        timeframe=req.timeframe,
        region=req.region,
        executive_summary=executive_summary,
        items=items
    )
    text = render_text(
        generated_at=generated_at,
        timeframe=req.timeframe,
        region=req.region,
        executive_summary=executive_summary,
        items=items
    )

    return BriefingResponse(
        generatedAt=generated_at,
        timeframe=req.timeframe,
        region=req.region,
        executiveSummary=executive_summary,
        items=items,
        html=html,
        text=text,
        subject=f"Film Investment Brief - {datetime.now().date().isoformat()}"
    )
