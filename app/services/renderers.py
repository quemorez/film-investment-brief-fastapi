from typing import List
from app.models.schemas import BriefingItem


def render_html(generated_at: str, timeframe: str, region: str, executive_summary: List[str], items: List[BriefingItem]) -> str:
    summary_html = "".join(f"<li>{line}</li>" for line in executive_summary)

    items_html = "".join(
        f'''
        <div style="padding:14px 0;border-top:1px solid #dbe3f0;">
          <h3 style="margin:0 0 6px 0;">{item.title}</h3>
          <div style="font-size:13px;color:#64748b;margin-bottom:8px;">{item.source} · {item.published}</div>
          <p style="margin:0 0 10px 0;">{item.summary}</p>
          <div style="background:#eef4ff;border-left:4px solid #2563eb;padding:10px 12px;border-radius:8px;">
            <strong>Why this matters for investors:</strong> {item.investorWhy}
          </div>
          <p style="margin:10px 0 0 0;"><a href="{item.url}" style="color:#2563eb;text-decoration:none;">Open source</a></p>
        </div>
        '''
        for item in items
    )

    return f'''
    <div style="font-family:Arial,Helvetica,sans-serif;max-width:860px;margin:0 auto;padding:24px;color:#0f172a;">
      <div style="background:#ffffff;border-radius:20px;padding:24px;box-shadow:0 12px 40px rgba(15,23,42,.08);">
        <h1 style="margin:0 0 8px 0;">Film Investment Brief</h1>
        <div style="font-size:14px;color:#64748b;margin-bottom:18px;">
          Generated: {generated_at}<br/>
          Timeframe: last {timeframe} day(s)<br/>
          Region: {region}
        </div>
        <h2 style="margin:0 0 8px 0;">Executive Summary</h2>
        <ul>{summary_html}</ul>
        <h2 style="margin:20px 0 10px 0;">Briefing Items</h2>
        {items_html}
      </div>
    </div>
    '''


def render_text(generated_at: str, timeframe: str, region: str, executive_summary: List[str], items: List[BriefingItem]) -> str:
    lines: List[str] = [
        "Film Investment Brief",
        f"Generated: {generated_at}",
        f"Timeframe: last {timeframe} day(s)",
        f"Region: {region}",
        "",
        "Executive Summary:",
    ]
    lines.extend(f"- {line}" for line in executive_summary)
    lines.append("")

    for item in items:
        lines.extend([
            item.title,
            f"Source: {item.source}",
            f"Published: {item.published}",
            f"Summary: {item.summary}",
            f"Why this matters for investors: {item.investorWhy}",
            f"Link: {item.url}",
            ""
        ])

    return "\n".join(lines)
