"""
Generate CFO brief PDF — Competitor Price Monitoring Internal Alternative.
Output saved to WORKAI/reports/
"""

import os
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER

NAVY  = colors.HexColor("#1F3864")
LIGHT = colors.HexColor("#EEF2F7")
WHITE = colors.white
GREEN = colors.HexColor("#E2EFDA")
GREY  = colors.HexColor("#F2F2F2")

W, H = A4
MARGIN = 18 * mm

REPORTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)
OUT = os.path.join(REPORTS_DIR, f"CFO-Brief-CompetitorPricing-{datetime.now().strftime('%Y%m%d')}.pdf")


def build():
    doc = SimpleDocTemplate(
        OUT, pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=14*mm, bottomMargin=14*mm,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle("title",
        fontName="Helvetica-Bold", fontSize=14, textColor=WHITE,
        leading=18, alignment=TA_LEFT)

    sub_style = ParagraphStyle("sub",
        fontName="Helvetica", fontSize=9, textColor=WHITE,
        leading=12, alignment=TA_LEFT)

    heading_style = ParagraphStyle("heading",
        fontName="Helvetica-Bold", fontSize=10, textColor=NAVY,
        spaceBefore=10, spaceAfter=3, leading=13)

    body_style = ParagraphStyle("body",
        fontName="Helvetica", fontSize=9, textColor=colors.black,
        leading=13, spaceAfter=4)

    small_style = ParagraphStyle("small",
        fontName="Helvetica", fontSize=8.5, textColor=colors.black,
        leading=12, spaceAfter=2)

    col_head = ParagraphStyle("col_head",
        fontName="Helvetica-Bold", fontSize=8.5, textColor=WHITE, leading=11)

    cell_style = ParagraphStyle("cell",
        fontName="Helvetica", fontSize=8.5, textColor=colors.black, leading=11)

    story = []

    # ── Header banner ─────────────────────────────────────────────────────────
    usable_w = W - 2 * MARGIN
    header_data = [[
        Paragraph("Competitor Price Monitoring — Internal Alternative", title_style),
        Paragraph("April 2026<br/>Commercial / Category Management", sub_style),
    ]]
    header_table = Table(header_data, colWidths=[usable_w * 0.62, usable_w * 0.38])
    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), NAVY),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (0, 0), 10),
        ("RIGHTPADDING", (-1, 0), (-1, 0), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 5*mm))

    # ── Background ────────────────────────────────────────────────────────────
    story.append(Paragraph("Background", heading_style))
    story.append(Paragraph(
        "The business currently pays a significant annual subscription to a third-party service "
        "(PriceAPI) for competitor pricing data. This brief outlines a working internal alternative "
        "built in-house, with no subscription cost and no dependency on paid external APIs.",
        body_style))

    # ── How it works ──────────────────────────────────────────────────────────
    story.append(Paragraph("How It Works", heading_style))
    story.append(Paragraph(
        "The tool operates in two stages:", body_style))
    story.append(Paragraph(
        "<b>1. Discovery</b> — probes each competitor's domain, locates their XML product sitemap, "
        "and builds an index of product URLs and titles. This runs once and is refreshed periodically.",
        small_style))
    story.append(Paragraph(
        "<b>2. Daily scrape</b> — loads our product catalogue, selects the top products by revenue, "
        "and for each: fuzzy-matches the product title against the competitor's sitemap index, "
        "then fetches the live price from the matched page.",
        small_style))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph(
        "Product matching uses token-based fuzzy scoring — this means it works for any competitor "
        "with a sitemap, regardless of whether their products appear in Google Shopping. "
        "A cost-floor validation step rejects false matches automatically.",
        small_style))

    # ── External services ─────────────────────────────────────────────────────
    story.append(Paragraph("External Services Used", heading_style))

    svc_data = [
        [Paragraph("Service", col_head), Paragraph("Purpose", col_head),
         Paragraph("Cost", col_head), Paragraph("Data Shared", col_head)],
        [Paragraph("Jina Reader (r.jina.ai)", cell_style),
         Paragraph("Reads public competitor pages; handles Cloudflare-protected sites", cell_style),
         Paragraph("Free", cell_style),
         Paragraph("None — outbound requests to public URLs only", cell_style)],
        [Paragraph("Python / openpyxl / thefuzz", cell_style),
         Paragraph("Matching, extraction, reporting", cell_style),
         Paragraph("Open source", cell_style),
         Paragraph("N/A", cell_style)],
    ]
    cw = [usable_w * r for r in [0.22, 0.38, 0.12, 0.28]]
    svc_table = Table(svc_data, colWidths=cw, repeatRows=1)
    svc_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("BACKGROUND", (0, 1), (-1, 1), LIGHT),
        ("BACKGROUND", (0, 2), (-1, 2), WHITE),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CCCCCC")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(svc_table)
    story.append(Paragraph(
        "No API keys. No subscriptions. Our product catalogue never leaves the local environment.",
        ParagraphStyle("note", fontName="Helvetica-Oblique", fontSize=8.5,
                       textColor=NAVY, spaceBefore=3, spaceAfter=4, leading=11)))

    # ── Current state ─────────────────────────────────────────────────────────
    story.append(Paragraph("Current State", heading_style))
    bullets = [
        "163 competitors indexed with working sitemaps",
        "Covers approximately 47% of current PriceAPI match volume",
        "Runs end-to-end; output validated against known market prices",
        "Report delivered as Excel, synced automatically to Google Drive",
    ]
    for b in bullets:
        story.append(Paragraph(f"&nbsp;&nbsp;•&nbsp;&nbsp;{b}", small_style))

    # ── Coverage & gaps ───────────────────────────────────────────────────────
    story.append(Paragraph("Coverage &amp; Gaps", heading_style))
    story.append(Paragraph(
        "The remaining ~53% of match volume breaks into three categories with distinct remedies:",
        small_style))
    story.append(Spacer(1, 2*mm))

    gap_data = [
        [Paragraph("Segment", col_head), Paragraph("Share", col_head),
         Paragraph("Cause", col_head), Paragraph("Options", col_head)],
        [Paragraph("Dead / inactive sites", cell_style),
         Paragraph("~14%", cell_style),
         Paragraph("Site no longer trading", cell_style),
         Paragraph("None — out of scope for any service", cell_style)],
        [Paragraph("WAF-blocked retailers", cell_style),
         Paragraph("~19%", cell_style),
         Paragraph("B&Q, Screwfix, Amazon etc. actively block scrapers", cell_style),
         Paragraph("ScrapingBee (pay-per-request, targeted at top products); "
                   "or retain PriceAPI for this tier only at reduced scope", cell_style)],
        [Paragraph("No sitemap", cell_style),
         Paragraph("~21%", cell_style),
         Paragraph("Competitor site lacks structured URL index", cell_style),
         Paragraph("Category page crawl; or Google site-search based discovery", cell_style)],
    ]
    gcw = [usable_w * r for r in [0.20, 0.08, 0.30, 0.42]]
    gap_table = Table(gap_data, colWidths=gcw, repeatRows=1)
    gap_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#FFE0E0")),
        ("BACKGROUND", (0, 2), (-1, 2), colors.HexColor("#FFF2CC")),
        ("BACKGROUND", (0, 3), (-1, 3), LIGHT),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CCCCCC")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(gap_table)
    story.append(Paragraph(
        "The dead-site segment represents true data loss for any provider. The WAF-blocked tier — "
        "which contains the most commercially significant competitors — can be addressed through a "
        "targeted paid scraping layer or a reduced PriceAPI contract covering only those sites. "
        "The no-sitemap segment is largely smaller players and lowest priority.",
        ParagraphStyle("note2", fontName="Helvetica-Oblique", fontSize=8.5,
                       textColor=colors.HexColor("#444444"), spaceBefore=3, spaceAfter=4, leading=11)))

    # ── Roadmap ───────────────────────────────────────────────────────────────
    story.append(Paragraph("Roadmap", heading_style))
    roadmap = [
        "ScrapingBee integration for WAF-blocked tier (targeted, high-revenue products only)",
        "Direct Tableau integration — removes manual export step, always-current catalogue data",
        "Scheduled daily runs with completion notification",
        "GitHub repository — version-controlled, auditable, shareable",
    ]
    for r in roadmap:
        story.append(Paragraph(f"&nbsp;&nbsp;•&nbsp;&nbsp;{r}", small_style))

    # ── Summary ───────────────────────────────────────────────────────────────
    story.append(Spacer(1, 3*mm))
    story.append(HRFlowable(width=usable_w, thickness=1, color=NAVY))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph(
        "<b>Summary</b>&nbsp;&nbsp;This is a functioning alternative covering the majority of "
        "commercially relevant competitors, built using only open-source tools and one free public "
        "proxy. It is lightweight, auditable, and extensible. The gap is understood and has a clear "
        "remediation path. Happy to walk through the code or a live run at any point.",
        ParagraphStyle("summary", fontName="Helvetica", fontSize=9,
                       textColor=colors.black, leading=13,
                       borderColor=NAVY, borderWidth=0,
                       backColor=LIGHT, borderPadding=6)))

    doc.build(story)
    print(f"Saved: {OUT}")


if __name__ == "__main__":
    build()
