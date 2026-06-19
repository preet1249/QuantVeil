"""
Cohere-themed PDF generator using ReportLab.
Produces two PDF formats:
  - generate_report_pdf() : A4 portrait, structured intelligence report
  - generate_slides_pdf() : Landscape, slide-like pages
"""
import os
import re
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, letter, landscape
from reportlab.lib.units import inch, mm
from reportlab.lib.colors import HexColor, white, black
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY

# ── Cohere Color Palette ──────────────────────────────────────────────────────
PRIMARY   = HexColor("#17171c")   # near-black
DEEPGREEN = HexColor("#003c33")   # deep green
CANVAS    = HexColor("#ffffff")   # white
STONE     = HexColor("#eeece7")   # soft stone
PALEGREEN = HexColor("#edfce9")   # pale green
HAIRLINE  = HexColor("#d9d9dd")   # hairline border
CARDBDR   = HexColor("#f2f2f2")   # card border
TEXT      = HexColor("#212121")   # ink
MUTED     = HexColor("#93939f")   # muted
BODYMUTED = HexColor("#616161")   # body-muted
CORAL     = HexColor("#ff7759")   # coral accent
GREEN     = HexColor("#2d6a4f")   # success green
RED       = HexColor("#b30000")   # error red
LIGHT     = HexColor("#93939f")   # alias

# legacy aliases used inside function bodies
NAVY   = DEEPGREEN
NAVYDK = PRIMARY
GOLD   = CORAL
OFFWHT = STONE
BORDER = HAIRLINE


# ── Report PDF (A4 portrait) ──────────────────────────────────────────────────

def generate_report_pdf(data: dict, output_dir: str = ".") -> str:
    domain   = re.sub(r"[^a-z0-9]", "_", data.get("domain", "report"))
    filename = f"report_{domain}.pdf"
    path     = os.path.join(output_dir, filename)

    doc = SimpleDocTemplate(
        path, pagesize=A4,
        leftMargin=0.7*inch, rightMargin=0.7*inch,
        topMargin=0.9*inch, bottomMargin=0.7*inch,
    )

    # ── Styles ────────────────────────────────────────────────────────────────
    styles = getSampleStyleSheet()

    def style(name, parent="Normal", **kw):
        s = ParagraphStyle(name, parent=styles[parent])
        for k, v in kw.items():
            setattr(s, k, v)
        return s

    s_title    = style("Title",   fontName="Times-Bold",   fontSize=28, textColor=white,
                        spaceAfter=4, alignment=TA_LEFT)
    s_h1       = style("H1",      fontName="Times-Bold",   fontSize=16, textColor=NAVY,
                        spaceBefore=14, spaceAfter=4)
    s_h2       = style("H2",      fontName="Helvetica-Bold", fontSize=12, textColor=NAVY,
                        spaceBefore=10, spaceAfter=3)
    s_label    = style("Label",   fontName="Helvetica-Bold", fontSize=8,  textColor=LIGHT,
                        spaceBefore=8, spaceAfter=2)
    s_body     = style("Body",    fontName="Helvetica",    fontSize=10, textColor=TEXT,
                        spaceBefore=2, spaceAfter=4, leading=15)
    s_mono     = style("Mono",    fontName="Courier",      fontSize=9,  textColor=NAVY,
                        spaceBefore=2, spaceAfter=2)
    s_muted    = style("Muted",   fontName="Helvetica",    fontSize=9,  textColor=MUTED,
                        spaceBefore=0, spaceAfter=2)
    s_quote    = style("Quote",   fontName="Times-Italic", fontSize=10, textColor=MUTED,
                        leftIndent=14, borderPadding=8, spaceBefore=4, spaceAfter=4)

    def _tbl_style(header_bg=NAVY):
        return TableStyle([
            ("BACKGROUND",  (0, 0), (-1,  0), header_bg),
            ("TEXTCOLOR",   (0, 0), (-1,  0), white),
            ("FONTNAME",    (0, 0), (-1,  0), "Helvetica-Bold"),
            ("FONTSIZE",    (0, 0), (-1,  0), 8),
            ("FONTNAME",    (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE",    (0, 1), (-1, -1), 9),
            ("TEXTCOLOR",   (0, 1), (-1, -1), TEXT),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, OFFWHT]),
            ("GRID",        (0, 0), (-1, -1), 0.5, BORDER),
            ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING",  (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ])

    def _hr(): return HRFlowable(width="100%", thickness=1, color=BORDER, spaceAfter=8)
    def _spacer(h=6): return Spacer(1, h)

    # ── Content builder ───────────────────────────────────────────────────────
    story = []

    contacts  = data.get("contacts", {})
    reddit    = data.get("reddit",   {})
    news_d    = data.get("news",     {})
    github    = data.get("github",   {})
    crunchbase = data.get("crunchbase", {})
    wayback   = data.get("wayback",  {})
    tech      = data.get("tech_stack", {})
    mkt       = data.get("market_research", "")
    cold      = data.get("cold_outreach", "")
    domain_v  = data.get("domain", "")
    title_v   = data.get("title", domain_v)

    # Cover block
    cover_data = [[Paragraph(
        f'<font color="white" size="22">{title_v[:60]}</font><br/>'
        f'<font color="#edfce9" size="10">{domain_v}</font><br/><br/>'
        f'<font color="#93939f" size="9">QUANTVEIL · INTELLIGENCE REPORT</font>',
        ParagraphStyle("cover", fontName="Helvetica", fontSize=22,
                       leading=30, textColor=white)
    )]]
    cover_tbl = Table(cover_data, colWidths=["100%"])
    cover_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), DEEPGREEN),
        ("TOPPADDING",    (0, 0), (-1, -1), 32),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 32),
        ("LEFTPADDING",   (0, 0), (-1, -1), 28),
        ("LINEBELOW",     (0, 0), (-1, -1), 1, CORAL),
    ]))
    story.append(cover_tbl)
    story.append(_spacer(16))

    # 1. Contacts
    story.append(Paragraph("CONTACT INTELLIGENCE", s_h1))
    story.append(_hr())
    emails  = contacts.get("emails",  [])
    phones  = contacts.get("phones",  [])
    socials = contacts.get("socials", {})
    if emails:
        story.append(Paragraph("Email Addresses", s_label))
        for e in emails:
            story.append(Paragraph(f"✉  {e}", s_mono))
    if phones:
        story.append(_spacer(6))
        story.append(Paragraph("Phone Numbers", s_label))
        for p in phones:
            story.append(Paragraph(f"☎  {p}", s_mono))
    if socials:
        story.append(_spacer(6))
        story.append(Paragraph("Social Media", s_label))
        rows = [["Platform", "URL"]] + [[k.title(), v[:60]] for k, v in list(socials.items())[:10]]
        t = Table(rows, colWidths=[1.2*inch, 5*inch])
        t.setStyle(_tbl_style())
        story.append(t)
    story.append(_spacer(12))

    # 2. Tech Stack
    if tech.get("all"):
        story.append(Paragraph("TECHNOLOGY STACK", s_h1))
        story.append(_hr())
        rows = [["Category", "Technologies"]]
        cat_labels = {"cms": "CMS/Platform", "framework": "JS Frameworks",
                      "ecommerce": "E-commerce", "analytics": "Analytics",
                      "marketing": "Marketing/CRM", "payments": "Payments",
                      "infrastructure": "Infrastructure"}
        for cat, label in cat_labels.items():
            techs = tech.get(cat, [])
            if techs:
                rows.append([label, ", ".join(techs)])
        t = Table(rows, colWidths=[1.8*inch, 5*inch])
        t.setStyle(_tbl_style())
        story.append(t)
        story.append(_spacer(12))

    # 3. Reddit
    story.append(Paragraph("REDDIT COMMUNITY INTELLIGENCE", s_h1))
    story.append(_hr())
    summary = reddit.get("ai_summary", "")
    if summary:
        story.append(Paragraph(summary[:800], s_body))
    posts = reddit.get("posts", [])[:8]
    if posts:
        story.append(_spacer(8))
        story.append(Paragraph("Top Posts", s_label))
        rows = [["Score", "Subreddit", "Title"]] + [
            [str(p.get("score", 0)), p.get("subreddit", ""), p.get("title", "")[:80]]
            for p in posts
        ]
        t = Table(rows, colWidths=[0.6*inch, 1.2*inch, 5*inch])
        t.setStyle(_tbl_style())
        story.append(t)
    story.append(_spacer(12))

    # 4. News
    news_items = news_d.get("news", [])[:8]
    hn_posts   = news_d.get("hn_posts", [])[:6]
    if news_items or hn_posts:
        story.append(Paragraph("NEWS & MEDIA", s_h1))
        story.append(_hr())
        if news_items:
            story.append(Paragraph("Google News", s_label))
            rows = [["Date", "Source", "Headline"]] + [
                [n.get("date", "")[:11], n.get("source", "")[:20], n.get("title", "")[:70]]
                for n in news_items
            ]
            t = Table(rows, colWidths=[1.0*inch, 1.2*inch, 4.6*inch])
            t.setStyle(_tbl_style())
            story.append(t)
        if hn_posts:
            story.append(_spacer(8))
            story.append(Paragraph("Hacker News", s_label))
            rows = [["Points", "Title"]] + [
                [str(h.get("points", 0)), h.get("title", "")[:90]] for h in hn_posts
            ]
            t = Table(rows, colWidths=[0.7*inch, 6.1*inch])
            t.setStyle(_tbl_style())
            story.append(t)
        story.append(_spacer(12))

    # 5. GitHub
    if github.get("has_org") or github.get("repos"):
        story.append(Paragraph("GITHUB INTELLIGENCE", s_h1))
        story.append(_hr())
        org = github.get("org", {})
        if org:
            story.append(Paragraph(
                f"<b>{org.get('name','')}</b> · {org.get('public_repos',0)} repos · "
                f"{org.get('followers',0)} followers · {org.get('location','')}",
                s_body
            ))
        repos = github.get("repos", [])[:6]
        if repos:
            rows = [["Repository", "Stars", "Language", "Updated"]] + [
                [r["name"], str(r["stars"]), r["language"], r["updated_at"]]
                for r in repos
            ]
            t = Table(rows, colWidths=[2.0*inch, 0.6*inch, 1.0*inch, 1.0*inch])
            t.setStyle(_tbl_style())
            story.append(t)
        story.append(_spacer(12))

    # 6. Crunchbase
    if crunchbase.get("found"):
        story.append(Paragraph("FUNDING & COMPANY DATA", s_h1))
        story.append(_hr())
        rows = [["Field", "Value"]]
        for key, label in [("founded","Founded"), ("headquarters","HQ"),
                            ("employee_count","Employees"), ("funding_total","Total Funding")]:
            v = crunchbase.get(key, "")
            if v:
                rows.append([label, v])
        if len(rows) > 1:
            t = Table(rows, colWidths=[1.5*inch, 5.3*inch])
            t.setStyle(_tbl_style())
            story.append(t)
        if crunchbase.get("investors"):
            story.append(_spacer(6))
            story.append(Paragraph("Investors: " + ", ".join(crunchbase["investors"]), s_body))
        story.append(_spacer(12))

    # 7. Market Research
    if mkt:
        story.append(Paragraph("MARKET INTELLIGENCE REPORT", s_h1))
        story.append(_hr())
        # Strip markdown formatting for PDF
        clean = re.sub(r"#+\s*", "", mkt)
        clean = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", clean)
        clean = re.sub(r"\*(.+?)\*", r"<i>\1</i>", clean)
        for para in clean.split("\n\n"):
            para = para.strip()
            if para:
                story.append(Paragraph(para[:600], s_body))
                story.append(_spacer(4))

    # 8. Cold Outreach
    if cold:
        story.append(Paragraph("COLD OUTREACH STRATEGY", s_h1))
        story.append(_hr())
        clean = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", cold)
        for para in clean.split("\n\n"):
            para = para.strip()
            if para:
                story.append(Paragraph(para[:600], s_body))
                story.append(_spacer(4))

    # Build
    def on_page(cvs, doc):
        cvs.saveState()
        w, h = A4
        # Top bar: thin deep-green strip
        cvs.setFillColor(DEEPGREEN)
        cvs.rect(0, h - 24, w, 24, fill=1, stroke=0)
        cvs.setFont("Helvetica-Bold", 7)
        cvs.setFillColor(white)
        cvs.drawString(0.7*inch, h - 15, "QUANTVEIL")
        cvs.drawRightString(w - 0.7*inch, h - 15, domain_v)
        # Bottom: hairline + page number
        cvs.setStrokeColor(HAIRLINE)
        cvs.line(0.7*inch, 0.55*inch, w - 0.7*inch, 0.55*inch)
        cvs.setFont("Helvetica", 7)
        cvs.setFillColor(MUTED)
        cvs.drawCentredString(w / 2, 0.38*inch, f"Page {doc.page}")
        cvs.restoreState()

    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    return path


# ── Slides PDF (landscape, PPT-style) ────────────────────────────────────────

def generate_slides_pdf(data: dict, output_dir: str = ".") -> str:
    """Generate landscape PDF that mirrors the 7 PPT slides."""
    domain   = re.sub(r"[^a-z0-9]", "_", data.get("domain", "report"))
    filename = f"slides_{domain}.pdf"
    path     = os.path.join(output_dir, filename)

    PW, PH = landscape(letter)  # 792 x 612 points
    c = canvas.Canvas(path, pagesize=landscape(letter))

    def _slide_header(title, subtitle=""):
        c.setFillColor(DEEPGREEN)
        c.rect(0, PH - 68, PW, 68, fill=1, stroke=0)
        c.setFillColor(CORAL)
        c.rect(0, PH - 70, PW, 2, fill=1, stroke=0)
        c.setFont("Helvetica-Bold", 20)
        c.setFillColor(white)
        c.drawString(36, PH - 40, title[:70])
        if subtitle:
            c.setFont("Helvetica", 9)
            c.setFillColor(HexColor("#86a8a4"))
            c.drawString(36, PH - 58, subtitle)

    def _slide_footer(page):
        c.setFont("Helvetica", 7)
        c.setFillColor(MUTED)
        c.drawString(36, 16, data.get("domain", ""))
        c.drawRightString(PW - 36, 16, f"{page} / 7")

    def _bg(color=None):
        if color:
            c.setFillColor(color)
            c.rect(0, 0, PW, PH, fill=1, stroke=0)

    def _para(x, y, w, text, font="Helvetica", size=10, color=TEXT, max_chars=80):
        if not text:
            return
        c.setFont(font, size)
        c.setFillColor(color)
        words = str(text).split()
        line, lines = [], []
        for word in words:
            test = " ".join(line + [word])
            if c.stringWidth(test, font, size) < w:
                line.append(word)
            else:
                if line:
                    lines.append(" ".join(line))
                line = [word]
        if line:
            lines.append(" ".join(line))
        for i, ln in enumerate(lines[:6]):
            c.drawString(x, y - i * (size + 2), ln)

    # ── Slide 1: Cover ────────────────────────────────────────────────────────
    _bg(DEEPGREEN)
    c.setFillColor(CORAL)
    c.rect(0, 0, 6, PH, fill=1, stroke=0)
    c.setFillColor(HexColor("#edfce9"))
    c.rect(6, PH * 0.44, PW - 6, 1, fill=1, stroke=0)
    c.setFont("Helvetica-Bold", 36)
    c.setFillColor(white)
    title_v = data.get("title", data.get("domain", ""))[:50]
    c.drawString(40, PH - 130, title_v)
    c.setFont("Helvetica", 12)
    c.setFillColor(HexColor("#86a8a4"))
    c.drawString(40, PH - 158, data.get("domain", ""))
    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(HexColor("#edfce9"))
    c.drawString(40, PH - 195, "INTELLIGENCE REPORT")
    _slide_footer(1)
    c.showPage()

    # ── Slide 2-7: Content ───────────────────────────────────────────────────
    slides_def = [
        ("Contact Intelligence",        _content_contacts),
        ("Market Position & Sentiment", _content_sentiment),
        ("Pain Points & Opportunities", _content_pain),
        ("Competitive Landscape",       _content_competitors),
        ("News & Media Timeline",       _content_news),
        ("Cold Outreach Strategy",      _content_outreach),
    ]

    for i, (slide_title, fn) in enumerate(slides_def, 2):
        _bg(OFFWHT)
        _slide_header(slide_title, data.get("domain", ""))
        fn(c, data, PW, PH)
        _slide_footer(i)
        c.showPage()

    c.save()
    return path


def _content_contacts(c, data, PW, PH):
    contacts = data.get("contacts", {})
    emails   = contacts.get("emails",  [])
    phones   = contacts.get("phones",  [])
    socials  = contacts.get("socials", {})
    y = PH - 95
    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(LIGHT)
    c.drawString(36, y, "EMAILS")
    y -= 18
    for e in emails[:6]:
        c.setFont("Courier", 10)
        c.setFillColor(NAVY)
        c.drawString(36, y, e)
        y -= 16
    y -= 6
    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(LIGHT)
    c.drawString(36, y, "PHONES")
    y -= 18
    for p in phones[:4]:
        c.setFont("Courier", 10)
        c.setFillColor(NAVY)
        c.drawString(36, y, p)
        y -= 16
    if socials:
        y -= 6
        c.setFont("Helvetica-Bold", 8)
        c.setFillColor(LIGHT)
        c.drawString(36, y, "SOCIAL PROFILES")
        y -= 18
        for platform, link in list(socials.items())[:6]:
            c.setFillColor(NAVY)
            c.rect(36, y - 4, 80, 16, fill=1, stroke=0)
            c.setFont("Helvetica-Bold", 8)
            c.setFillColor(white)
            c.drawString(40, y + 1, platform.upper()[:12])
            c.setFont("Helvetica", 8)
            c.setFillColor(TEXT)
            c.drawString(124, y + 1, link[:55])
            y -= 20


def _content_sentiment(c, data, PW, PH):
    reddit  = data.get("reddit",  {})
    wayback = data.get("wayback", {})
    summary = reddit.get("ai_summary", "No data.")[:500]
    trend   = wayback.get("trend", "unknown")

    y = PH - 98
    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(LIGHT)
    c.drawString(36, y, "REDDIT INTELLIGENCE SUMMARY")
    y -= 14

    c.setFillColor(HexColor("#F5F5F5"))
    c.rect(36, y - 120, PW / 2 - 50, 126, fill=1, stroke=0)
    c.setFont("Helvetica", 9)
    c.setFillColor(TEXT)
    for line in summary.split("\n")[:10]:
        c.drawString(44, y - 4, line[:65])
        y -= 13

    # Growth signal box
    sx = PW / 2 + 20
    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(LIGHT)
    c.drawString(sx, PH - 98, "GROWTH SIGNAL")
    trend_colors = {"growing": GREEN, "shrinking": RED, "stable": NAVY}
    trend_labels = {"growing": "↑ GROWING", "shrinking": "↓ SHRINKING", "stable": "→ STABLE"}
    tc = trend_colors.get(trend, MUTED)
    c.setFillColor(tc)
    c.rect(sx, PH - 128, 120, 22, fill=1, stroke=0)
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(white)
    c.drawString(sx + 8, PH - 119, trend_labels.get(trend, trend.upper()))
    c.setFont("Helvetica", 9)
    c.setFillColor(TEXT)
    c.drawString(sx, PH - 145, wayback.get("summary", "")[:60])


def _content_pain(c, data, PW, PH):
    mkt = data.get("market_research", "")

    def _extract(section):
        m = re.search(rf"{section}.*?\n(.*?)(?=\n##|\Z)", mkt, re.S | re.I)
        if not m:
            return ["Limited data available."]
        bullets = re.findall(r"[WOST]\d+\.\s+(.+?)(?=\n[WOST]|\n##|\Z)", m.group(1), re.S)
        if not bullets:
            bullets = [l.strip("- •*").strip() for l in m.group(1).splitlines()
                       if len(l.strip()) > 10]
        return bullets[:5]

    half = (PW - 72) / 2
    y0 = PH - 98

    # Pain points (left)
    c.setFillColor(RED)
    c.rect(36, y0 - 160, 4, 164, fill=1, stroke=0)
    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(RED)
    c.drawString(48, y0, "PAIN POINTS / WEAKNESSES")
    y = y0 - 18
    for item in _extract("WEAKNESSES"):
        c.setFillColor(GOLD)
        c.circle(54, y + 3, 3, fill=1, stroke=0)
        c.setFont("Helvetica", 9)
        c.setFillColor(TEXT)
        c.drawString(64, y, item[:60])
        y -= 16

    # Opportunities (right)
    rx = PW / 2 + 10
    c.setFillColor(GREEN)
    c.rect(rx, y0 - 160, 4, 164, fill=1, stroke=0)
    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(GREEN)
    c.drawString(rx + 12, y0, "OPPORTUNITIES")
    y = y0 - 18
    for item in _extract("OPPORTUNITIES"):
        c.setFillColor(GOLD)
        c.circle(rx + 18, y + 3, 3, fill=1, stroke=0)
        c.setFont("Helvetica", 9)
        c.setFillColor(TEXT)
        c.drawString(rx + 28, y, item[:60])
        y -= 16


def _content_competitors(c, data, PW, PH):
    mkt = data.get("market_research", "")
    m   = re.search(r"COMPETITIVE LANDSCAPE(.*?)(?=\n##|\Z)", mkt, re.S | re.I)
    lines = []
    if m:
        for ln in m.group(1).splitlines():
            ln = ln.strip("- •*").strip()
            if len(ln) > 8 and not ln.startswith("#"):
                lines.append(ln[:90])

    y = PH - 96
    for i, ln in enumerate(lines[:10]):
        bg = HexColor("#FFFFFF") if i % 2 == 0 else OFFWHT
        c.setFillColor(bg)
        c.rect(36, y - 8, PW - 72, 22, fill=1, stroke=0)
        c.setFillColor(NAVY)
        c.rect(36, y - 8, 4, 22, fill=1, stroke=0)
        c.setFont("Helvetica", 9)
        c.setFillColor(TEXT)
        c.drawString(48, y + 1, ln)
        y -= 24
        if y < 60:
            break


def _content_news(c, data, PW, PH):
    news_d   = data.get("news", {})
    news     = news_d.get("news", [])[:6]
    hn_posts = news_d.get("hn_posts", [])[:5]
    half     = PW / 2 - 20

    y = PH - 96
    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(LIGHT)
    c.drawString(36, y, "GOOGLE NEWS")
    y -= 16
    for item in news:
        c.setFont("Helvetica", 7)
        c.setFillColor(MUTED)
        c.drawString(36, y, f"{item.get('date','')[:11]}  ·  {item.get('source','')[:20]}")
        y -= 12
        c.setFont("Helvetica", 9)
        c.setFillColor(TEXT)
        c.drawString(36, y, item.get("title", "")[:65])
        y -= 16
        c.setFillColor(BORDER)
        c.line(36, y + 4, half, y + 4)
        y -= 6
        if y < 60:
            break

    rx = PW / 2 + 10
    y2 = PH - 96
    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(LIGHT)
    c.drawString(rx, y2, "HACKER NEWS")
    y2 -= 16
    for post in hn_posts:
        pts = post.get("points", 0)
        c.setFillColor(GOLD)
        c.rect(rx, y2 - 4, 38, 16, fill=1, stroke=0)
        c.setFont("Helvetica-Bold", 8)
        c.setFillColor(NAVYDK)
        c.drawString(rx + 3, y2, f"{pts}pts")
        c.setFont("Helvetica", 9)
        c.setFillColor(TEXT)
        c.drawString(rx + 46, y2, post.get("title", "")[:55])
        y2 -= 20
        if y2 < 60:
            break


def _content_outreach(c, data, PW, PH):
    cold = data.get("cold_outreach", "")
    if not cold:
        c.setFont("Helvetica", 10)
        c.setFillColor(MUTED)
        c.drawString(36, PH - 120, "Enable AI analysis to generate outreach strategy.")
        return

    opening_m = re.search(r"(?:Opening Line|OPENING LINE)[:\s]*\"?(.+?)\"?\n", cold, re.I)
    opening   = opening_m.group(1).strip()[:160] if opening_m else cold[:160]

    y = PH - 96
    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(LIGHT)
    c.drawString(36, y, "OPENING LINE")
    y -= 14

    c.setFillColor(HexColor("#F5EDD4"))
    c.rect(36, y - 36, PW - 72, 42, fill=1, stroke=0)
    c.setFillColor(GOLD)
    c.rect(36, y - 36, 4, 42, fill=1, stroke=0)
    c.setFont("Times-Italic", 11)
    c.setFillColor(NAVYDK)
    c.drawString(48, y - 6, f'"{opening[:75]}"')
    if len(opening) > 75:
        c.drawString(48, y - 20, f'"{opening[75:150]}"')

    y -= 55
    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(LIGHT)
    c.drawString(36, y, "STRATEGY POINTS")
    y -= 16

    bullets = [ln.strip("- •*#").strip() for ln in cold.splitlines()
               if len(ln.strip("- •*#").strip()) > 15 and not "Opening" in ln]
    for bullet in bullets[:7]:
        c.setFillColor(GOLD)
        c.circle(44, y + 3, 3, fill=1, stroke=0)
        c.setFont("Helvetica", 9)
        c.setFillColor(TEXT)
        c.drawString(56, y, bullet[:75])
        y -= 18
        if y < 60:
            break
