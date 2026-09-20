"""
Generates a professional, print-ready PDF snapshot of the Sovereign Capital
Flow Dashboard: an executive summary followed by one section per curated
dataset. Built with reportlab (Platypus) so it has no system dependencies
beyond the pure-Python package itself.

Usage (see app.py):
    from utils.pdf_report import generate_report_pdf
    pdf_bytes = generate_report_pdf(datasets, meta)
    st.download_button("Download PDF", data=pdf_bytes, file_name="...", mime="application/pdf")
"""
from io import BytesIO
from datetime import datetime
import re

from reportlab.lib.pagesizes import LETTER, landscape
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak,
    HRFlowable, KeepTogether,
)

# reportlab's built-in (AFM) fonts have no emoji glyphs — an emoji renders as
# a solid black box instead of failing loudly, so strip it defensively from
# any text before it reaches a Paragraph or canvas draw call.
_EMOJI_RE = re.compile(
    "["
    "\U0001F300-\U0001FAFF"
    "\U00002600-\U000027BF"
    "\U0001F1E6-\U0001F1FF"
    "\U00002190-\U000021FF"  # arrows (safe to drop; not used as data)
    "\U0000FE0F"             # variation selector-16
    "\U0000200D"             # zero-width joiner
    "]+"
)


def _strip_emoji(text: str) -> str:
    if text is None:
        return text
    return _EMOJI_RE.sub("", str(text)).strip()

# ---------------------------------------------------------------------------
# Palette — echoes the dashboard's dark/gold theme, adapted for print (white
# background; gold/navy used only as accents so it stays legible on paper).
# ---------------------------------------------------------------------------
NAVY = colors.HexColor("#14161c")
GOLD = colors.HexColor("#c9971f")
GOLD_LIGHT = colors.HexColor("#f2e6c8")
GREY = colors.HexColor("#6b7280")
ROW_ALT = colors.HexColor("#f7f7f5")
GREEN = colors.HexColor("#2e7d46")
AMBER = colors.HexColor("#b8860b")
RED = colors.HexColor("#b23a3a")

PAGE_SIZE = landscape(LETTER)
MARGIN = 0.5 * inch
CONTENT_WIDTH = PAGE_SIZE[0] - 2 * MARGIN

styles = getSampleStyleSheet()
styles.add(ParagraphStyle("ReportTitle", fontSize=26, leading=30, textColor=NAVY,
                           spaceAfter=6, fontName="Helvetica-Bold"))
styles.add(ParagraphStyle("ReportSubtitle", fontSize=13, leading=16, textColor=GREY,
                           spaceAfter=4, fontName="Helvetica"))
styles.add(ParagraphStyle("SectionHeading", fontSize=16, leading=19, textColor=NAVY,
                           spaceBefore=4, spaceAfter=8, fontName="Helvetica-Bold"))
styles.add(ParagraphStyle("SectionSub", fontSize=9.5, leading=12, textColor=GREY,
                           spaceAfter=10, fontName="Helvetica-Oblique"))
styles.add(ParagraphStyle("CellText", fontSize=7.6, leading=9.2, fontName="Helvetica"))
styles.add(ParagraphStyle("CellTextBold", fontSize=7.6, leading=9.2, fontName="Helvetica-Bold"))
styles.add(ParagraphStyle("CellHeader", fontSize=8, leading=10, textColor=colors.white,
                           fontName="Helvetica-Bold"))
styles.add(ParagraphStyle("Footnote", fontSize=7.5, leading=9, textColor=GREY))
styles.add(ParagraphStyle("KPILabel", fontSize=8.5, textColor=GREY, fontName="Helvetica"))
styles.add(ParagraphStyle("KPIValue", fontSize=13, leading=15, textColor=NAVY, fontName="Helvetica-Bold"))


def _p(text, style="CellText"):
    """Wrap a value as a Paragraph so long text wraps inside table cells."""
    if text is None or (isinstance(text, float) and text != text):  # NaN check
        text = ""
    text = str(text)
    if text.lower() == "nan":
        text = ""
    text = _strip_emoji(text)
    # Paragraph treats bare & < > as XML — escape defensively.
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return Paragraph(text, styles[style])


def _df_table(df, col_weights=None, header_bg=NAVY, font_size=7.6, max_rows=None):
    """
    Render a DataFrame as a wrapped, styled Platypus Table sized to the page.
    col_weights: optional list of relative widths (same length as columns);
    defaults to a heuristic based on each column's average text length.
    """
    if max_rows:
        df = df.head(max_rows)

    cols = list(df.columns)
    if col_weights is None:
        col_weights = []
        for c in cols:
            lengths = df[c].map(lambda v: len(str(v)) if v is not None else 0)
            avg_len = lengths.mean() if len(df) else len(str(c))
            col_weights.append(max(avg_len, len(str(c)), 4))
    total_weight = sum(col_weights)
    col_widths = [CONTENT_WIDTH * (w / total_weight) for w in col_weights]

    header_row = [Paragraph(str(c).replace("_", " ").title(), styles["CellHeader"]) for c in cols]
    body_rows = []
    for _, row in df.iterrows():
        body_rows.append([_p(row[c]) for c in cols])

    data = [header_row] + body_rows
    table = Table(data, colWidths=col_widths, repeatRows=1)

    style_cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), header_bg),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("FONTSIZE", (0, 0), (-1, -1), font_size),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#d8dadf")),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]
    for i in range(1, len(data)):
        if i % 2 == 0:
            style_cmds.append(("BACKGROUND", (0, i), (-1, i), ROW_ALT))
    table.setStyle(TableStyle(style_cmds))
    return table


def _section(title, subtitle, flowables_after_heading):
    """A page section: heading + optional subtitle + a list of flowables."""
    block = [Paragraph(title, styles["SectionHeading"])]
    if subtitle:
        block.append(Paragraph(subtitle, styles["SectionSub"]))
    block += flowables_after_heading
    return block


def _kpi_cell(label, value, signal=None):
    sig_color = {"hot": GOLD, "ok": GREEN, "neg": RED}.get(signal, GREY)
    rows = [
        [Paragraph(label, styles["KPILabel"])],
        [Paragraph(str(value), styles["KPIValue"])],
    ]
    t = Table(rows, colWidths=[CONTENT_WIDTH / 4 - 10])
    t.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.75, sig_color),
        ("LINEBELOW", (0, 0), (0, 0), 0, colors.white),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    return t


def _footer(canvas_obj, doc):
    canvas_obj.saveState()
    canvas_obj.setStrokeColor(colors.HexColor("#d8dadf"))
    canvas_obj.line(MARGIN, 0.4 * inch, PAGE_SIZE[0] - MARGIN, 0.4 * inch)
    canvas_obj.setFont("Helvetica", 7.5)
    canvas_obj.setFillColor(GREY)
    canvas_obj.drawString(MARGIN, 0.25 * inch,
                           "Sovereign Capital Flow Dashboard — Educational research report, not investment advice.")
    canvas_obj.drawRightString(PAGE_SIZE[0] - MARGIN, 0.25 * inch, f"Page {doc.page}")
    canvas_obj.restoreState()


def generate_report_pdf(datasets: dict, meta: dict) -> bytes:
    """
    datasets: dict of dataset_name -> pandas DataFrame, expected keys:
        cofer, gold_annual, gold_buyers, swift_rmb, cbdc, energy,
        swf, institutional, bonds_fiscal, refresh_log
    meta: dict with precomputed dashboard summary values, expected keys:
        generated_at (str), rdi (int), cards (list of dicts with
        keys: level, title, sub, value, signal)
    Returns: PDF file content as bytes.
    """
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=PAGE_SIZE,
        leftMargin=MARGIN, rightMargin=MARGIN, topMargin=MARGIN, bottomMargin=0.55 * inch,
        title="Sovereign Capital Flow Dashboard Report",
        author="Sovereign Capital Flow Dashboard",
    )

    story = []

    # ---------------- Cover ----------------
    story.append(Spacer(1, 1.6 * inch))
    story.append(Paragraph(_strip_emoji("🏛️ Sovereign Capital Flow Dashboard"), styles["ReportTitle"]))
    story.append(Paragraph("Central bank reserves, gold flows, payment rails, energy settlement,"
                            " sovereign wealth deals &amp; fiscal signals", styles["ReportSubtitle"]))
    story.append(Spacer(1, 0.25 * inch))
    story.append(HRFlowable(width=3 * inch, thickness=1.4, color=GOLD, hAlign="LEFT"))
    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph(f"Generated {meta.get('generated_at', datetime.now().strftime('%Y-%m-%d %H:%M UTC'))}",
                            styles["Footnote"]))
    story.append(Paragraph("Educational research dashboard — not investment advice. "
                            "Curated datasets are periodic snapshots; verify against official sources "
                            "before relying on any figure.", styles["Footnote"]))
    story.append(PageBreak())

    # ---------------- Executive summary ----------------
    story.append(Paragraph("Executive Summary", styles["SectionHeading"]))
    story.append(Paragraph(f"Reserve Diversification Index: <b>{meta.get('rdi', '—')}</b> / 100 "
                            "(0 = full dollar hegemony · 100 = advanced multipolar rails)",
                            styles["SectionSub"]))
    story.append(Spacer(1, 6))

    cards = meta.get("cards", [])
    kpi_rows = []
    row = []
    for i, c in enumerate(cards):
        cell_stack = [
            Paragraph(_strip_emoji(f"LEVEL {c['level']} — {c['title']}"), styles["KPILabel"]),
            Spacer(1, 2),
            Paragraph(_strip_emoji(c["sub"]), styles["Footnote"]),
            Spacer(1, 3),
            Paragraph(_strip_emoji(str(c["value"])), styles["KPIValue"]),
        ]
        sig_color = {"hot": GOLD, "ok": GREEN, "neg": RED}.get(c.get("signal"), GREY)
        cell_table = Table([[cell_stack]], colWidths=[CONTENT_WIDTH / 4 - 8])
        cell_table.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 1, sig_color),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ]))
        row.append(cell_table)
        if len(row) == 4 or i == len(cards) - 1:
            kpi_rows.append(row)
            row = []
    for r in kpi_rows:
        wrapper = Table([r], colWidths=[CONTENT_WIDTH / 4] * len(r))
        wrapper.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 3),
                                      ("RIGHTPADDING", (0, 0), (-1, -1), 3)]))
        story.append(wrapper)
        story.append(Spacer(1, 8))
    story.append(PageBreak())

    # ---------------- Section 1: Central Bank Reserves (COFER) ----------------
    cofer = datasets.get("cofer")
    if cofer is not None and len(cofer):
        story += _section(
            "1 · Central Bank Reserves — IMF COFER",
            "Allocated foreign-exchange reserve shares by currency, historical series.",
            [_df_table(cofer, font_size=7.8)],
        )
        story.append(PageBreak())

    # ---------------- Section 2: Central-Bank Gold ----------------
    gold_a = datasets.get("gold_annual")
    gold_b = datasets.get("gold_buyers")
    gold_flow = []
    if gold_a is not None and len(gold_a):
        gold_flow.append(Paragraph("Net annual central-bank gold purchases (tonnes)", styles["CellTextBold"]))
        gold_flow.append(Spacer(1, 4))
        gold_flow.append(_df_table(gold_a, font_size=8))
        gold_flow.append(Spacer(1, 12))
    if gold_b is not None and len(gold_b):
        gold_flow.append(Paragraph("Top individual buyers by year (tonnes)", styles["CellTextBold"]))
        gold_flow.append(Spacer(1, 4))
        gold_flow.append(_df_table(gold_b, font_size=7.8))
    if gold_flow:
        story += _section(
            "2 · Central-Bank Gold Buying — World Gold Council",
            "Official-sector gold demand, aggregate and by leading buyer.",
            gold_flow,
        )
        story.append(PageBreak())

    # ---------------- Section 3: Sovereign Wealth Funds ----------------
    swf = datasets.get("swf")
    if swf is not None and len(swf):
        story += _section(
            "3 · Sovereign Wealth Fund Deals — SEC EDGAR 13F + Global SWF",
            "Tracked SWF transactions and portfolio shifts, most recent first.",
            [_df_table(swf.iloc[::-1].reset_index(drop=True), font_size=7.3)],
        )
        story.append(PageBreak())

    # ---------------- Section 4: Energy Settlement ----------------
    energy = datasets.get("energy")
    if energy is not None and len(energy):
        story += _section(
            "4 · Energy Settlement Corridors — Reuters + Ministry Statements",
            "Non-USD / alternative-currency energy trade settlement corridors.",
            [_df_table(energy, font_size=7.5)],
        )
        story.append(PageBreak())

    # ---------------- Section 5: Payment Rails ----------------
    rmb = datasets.get("swift_rmb")
    cbdc = datasets.get("cbdc")
    rails_flow = []
    if rmb is not None and len(rmb):
        rails_flow.append(Paragraph("RMB share of SWIFT global payments, by month (%)", styles["CellTextBold"]))
        rails_flow.append(Spacer(1, 4))
        rails_flow.append(_df_table(rmb, font_size=8))
        rails_flow.append(Spacer(1, 12))
    if cbdc is not None and len(cbdc):
        rails_flow.append(Paragraph("Central Bank Digital Currency status by jurisdiction", styles["CellTextBold"]))
        rails_flow.append(Spacer(1, 4))
        rails_flow.append(_df_table(cbdc, font_size=7.4))
    if rails_flow:
        story += _section(
            "5 · Payment Rails — SWIFT &amp; Atlantic Council CBDC Tracker",
            "Parallel payment infrastructure: RMB internationalization and CBDC rollout.",
            rails_flow,
        )
        story.append(PageBreak())

    # ---------------- Section 6: Fiscal & Bond Markets ----------------
    bonds = datasets.get("bonds_fiscal")
    if bonds is not None and len(bonds):
        story += _section(
            "6 · Fiscal &amp; Bond Markets — IMF Fiscal Monitor / WEO",
            "Government debt-to-GDP and interest-burden signals for major economies.",
            [_df_table(bonds, font_size=7.6)],
        )
        story.append(PageBreak())

    # ---------------- Section 7: Institutional Stack ----------------
    inst = datasets.get("institutional")
    if inst is not None and len(inst):
        story += _section(
            "7 · Institutional Stack — SEC EDGAR + Issuer Announcements",
            "Custody, BTC ETF exposure, tokenization and stablecoin activity by institution.",
            [_df_table(inst, font_size=7.0)],
        )
        story.append(PageBreak())

    # ---------------- Appendix: Data Freshness Log ----------------
    log = datasets.get("refresh_log")
    if log is not None and len(log):
        story += _section(
            "Appendix · Data Freshness Log",
            "Snapshot date and expected refresh cadence for every curated dataset.",
            [_df_table(log, font_size=7.6)],
        )

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return buf.getvalue()
