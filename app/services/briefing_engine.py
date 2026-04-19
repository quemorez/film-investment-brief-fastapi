from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from app.models.schemas import BriefingItem, BriefingRequest, BriefingResponse
from app.services.renderers import render_html, render_text
from app.services.source_fetchers import fetch_feed_items, fetch_data_page_items, RawItem


KEYWORDS = {
    "investment": [
        "investment", "invest", "fund", "capital", "financing", "financed",
        "equity", "stake", "deal", "acquisition", "merger", "buyout"
    ],
    "audience": [
        "audience", "viewing", "ratings", "subscriber", "subscribers",
        "streaming", "watch time", "engagement"
    ],
    "new_media": [
        "creator", "creators", "youtube", "shorts", "podcast",
        "digital", "new media", "influencer"
    ],
    "incentives": [
        "incentive", "rebate", "tax credit", "tax incentive",
        "production support", "co-production", "coproduction"
    ],
    "film_tv": [
        "film", "tv", "television", "studio", "box office",
        "distribution", "series", "movie", "cinema"
    ],
    "international": [
        "international", "global", "europe", "asia", "uae", "saudi",
        "canada", "australia", "india", "uk", "france", "germany"
    ],
}


def dedupe_items(items: List[RawItem]) -> List[RawItem]:
    seen = set()
    out: List[RawItem] = []
    for item in items:
        key = "".join(ch for ch in item.title.lower() if ch.isalnum())[:140]
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


def score_text(text: str) -> int:
    t = text.lower()
    score = 0

    for words in KEYWORDS.values():
        for w in words:
            if w in t:
                score += 2

    if any(x in t for x in ["netflix", "disney", "warner", "amazon", "apple", "paramount", "youtube"]):
        score += 2

    if any(x in t for x in ["private equity", "sovereign wealth", "financing", "funding round"]):
        score += 3

    return score


def matches_region(item: RawItem, region: str) -> bool:
    if region == "both":
        return True
    return item.region in (region, "both")


def matches_categories(item: RawItem, categories: List[str]) -> bool:
    if not categories:
        return True

    t = f"{item.title} {item.body}".lower()
    wanted = {c.lower() for c in categories}

    checks = {
        "film": any(x in t for x in KEYWORDS["film_tv"]),
        "tv": any(x in t for x in ["tv", "television", "series", "streaming"]),
        "new_media": any(x in t for x in KEYWORDS["new_media"]),
        "investment": any(x in t for x in KEYWORDS["investment"]),
        "incentives": any(x in t for x in KEYWORDS["incentives"]),
    }

    return any(checks.get(cat, False) for cat in wanted)


def classify_section(text: str) -> str:
    t = text.lower()

    if any(x in t for x in ["deal", "acquisition", "stake", "fund", "capital", "financing", "buyout", "merger"]):
        return "Investment / Deals"
    if any(x in t for x in ["creator", "youtube", "podcast", "shorts", "digital", "new media"]):
        return "New Media / Creator Economy"
    if any(x in t for x in ["audience", "ratings", "viewing", "subscriber", "streaming", "watch time"]):
        return "Audience / Platform Trends"
    if any(x in t for x in KEYWORDS["international"]):
        return "International"
    return "General Industry"


def simple_summary(item: RawItem) -> str:
    body = " ".join(item.body.split())
    if not body:
        return item.title

    sentences = body.split(". ")
    picked: List[str] = []

    for s in sentences:
        s = s.strip()
        if len(s) < 30:
            continue
        picked.append(s.rstrip("."))
        if len(picked) == 2:
            break

    summary = ". ".join(picked).strip()
    if not summary:
        summary = body[:280].strip()

    if len(summary) > 340:
        summary = summary[:337].rstrip() + "..."
    elif not summary.endswith("."):
        summary += "."

    return summary


def investor_relevance(item: RawItem) -> str:
    text = f"{item.title} {item.body}".lower()

    if any(k in text for k in ["acquisition", "merger", "stake", "equity", "buyout", "deal"]):
        return "This signals where ownership and leverage are concentrating, which can affect valuation, distribution power, and control of future slates."
    if any(k in text for k in ["financing", "fund", "capital", "investment", "co-production", "coproduction"]):
        return "This points to where money is opening up or tightening, which matters for financing strategy, partner selection, and timing."
    if any(k in text for k in ["streaming", "audience", "viewing", "ratings", "subscriber"]):
        return "This helps show where viewer attention is moving, which platforms are gaining traction, and what kinds of content are commercially stronger."
    if any(k in text for k in ["youtube", "creator", "shorts", "podcast", "digital", "new media"]):
        return "This highlights how creator-led media is competing with traditional film and TV for attention, ad dollars, and intellectual property value."
    if any(k in text for k in KEYWORDS["international"]):
        return "This matters because growth, incentives, and co-financing opportunities are often coming from outside the US, which can reshape where projects get made and funded."
    if any(k in text for k in ["incentive", "rebate", "tax credit", "production support"]):
        return "This is useful for evaluating where production capital can go further and which territories may offer stronger returns through incentives or lower costs."
    return "This may affect market sentiment, project packaging, audience demand, or the near-term direction of media investment."


def build_executive_summary(items: List[BriefingItem]) -> List[str]:
    if not items:
        return ["No strong items were found for the selected timeframe and filters."]

    lines: List[str] = []

    top_sections = [item.section for item in items[:5]]

    if any(s == "Investment / Deals" for s in top_sections):
        lines.append("Capital and deal activity remain important drivers of where media power and project leverage are concentrating.")
    if any(s == "International" for s in top_sections):
        lines.append("International markets and incentives continue to matter because they can materially change production economics and financing structure.")
    if any(s == "Audience / Platform Trends" for s in top_sections):
        lines.append("Audience behavior and platform movement remain critical because attention shifts directly affect monetization and content strategy.")
    if any(s == "New Media / Creator Economy" for s in top_sections):
        lines.append("Creator-led ecosystems continue to matter as sources of audience, intellectual property, and monetization growth.")

    if not lines:
        lines.append("The current briefing points to continued overlap between media strategy, audience movement, and capital allocation.")

    return lines[:3]


def generate_briefing_payload(req: BriefingRequest) -> BriefingResponse:
    generated_at = datetime.now(timezone.utc).isoformat()

    raw_items = fetch_feed_items(days=int(req.timeframe), max_per_feed=20)
    raw_items += fetch_data_page_items()
    raw_items = dedupe_items(raw_items)

    filtered: List[tuple[int, RawItem]] = []

    for item in raw_items:
        if not matches_region(item, req.region):
            continue
        if not matches_categories(item, req.categories):
            continue

        haystack = f"{item.title} {item.body}"
        score = score_text(haystack)

        if score < 2:
            continue

        filtered.append((score, item))

    filtered.sort(key=lambda x: x[0], reverse=True)

    top_items = filtered[:12]

    items: List[BriefingItem] = []
    for _, raw in top_items:
        text = f"{raw.title} {raw.body}"
        items.append(
            BriefingItem(
                title=raw.title,
                source=raw.source,
                url=raw.url,
                published=raw.published or generated_at,
                summary=simple_summary(raw),
                investorWhy=investor_relevance(raw),
                section=classify_section(text),
            )
        )

    executive_summary = build_executive_summary(items)

    html = render_html(
        generated_at=generated_at,
        timeframe=req.timeframe,
        region=req.region,
        executive_summary=executive_summary,
        items=items,
    )
    text = render_text(
        generated_at=generated_at,
        timeframe=req.timeframe,
        region=req.region,
        executive_summary=executive_summary,
        items=items,
    )

    return BriefingResponse(
        generatedAt=generated_at,
        timeframe=req.timeframe,
        region=req.region,
        executiveSummary=executive_summary,
        items=items,
        html=html,
        text=text,
        subject=f"Film Investment Brief - {datetime.now().date().isoformat()}",
    )
