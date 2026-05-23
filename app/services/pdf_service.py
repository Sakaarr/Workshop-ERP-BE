import io
from decimal import Decimal
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, black, white
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.pdfgen import canvas as pdfcanvas
from reportlab.lib import colors

# Brand colors
BRAND_AMBER = HexColor("#f59e0b")
BRAND_DARK  = HexColor("#1a1a1a")
BRAND_GRAY  = HexColor("#6b7280")
BRAND_LIGHT = HexColor("#f9fafb")
BRAND_LINE  = HexColor("#e5e7eb")
SUCCESS     = HexColor("#16a34a")
DANGER      = HexColor("#dc2626")


def _header_canvas(canvas, doc, title: str, subtitle: str):
    canvas.saveState()
    w, h = A4

    # Top amber bar
    canvas.setFillColor(BRAND_AMBER)
    canvas.rect(0, h - 18 * mm, w, 18 * mm, fill=True, stroke=False)

    # Company name in bar
    canvas.setFillColor(BRAND_DARK)
    canvas.setFont("Helvetica-Bold", 13)
    canvas.drawString(15 * mm, h - 11 * mm, "Auto Garden Pvt. Ltd.")
    canvas.setFont("Helvetica", 8)
    canvas.drawString(15 * mm, h - 15.5 * mm, "Bharatpur, Chitwan, Nepal")

    # Doc type top-right
    canvas.setFont("Helvetica-Bold", 11)
    canvas.drawRightString(w - 15 * mm, h - 10 * mm, title)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(BRAND_DARK)
    canvas.drawRightString(w - 15 * mm, h - 15 * mm, subtitle)

    # Footer line
    canvas.setStrokeColor(BRAND_LINE)
    canvas.setLineWidth(0.5)
    canvas.line(15 * mm, 12 * mm, w - 15 * mm, 12 * mm)
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(BRAND_GRAY)
    canvas.drawString(15 * mm, 8 * mm, "Auto Garden Pvt. Ltd. · Bharatpur, Chitwan · PAN: XXXXXXXXX")
    canvas.drawRightString(w - 15 * mm, 8 * mm, f"Page {doc.page}")

    canvas.restoreState()


def generate_invoice_pdf(invoice_data: dict) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=28 * mm,
        bottomMargin=22 * mm,
    )

    styles = getSampleStyleSheet()
    normal  = ParagraphStyle("n", fontName="Helvetica", fontSize=9, leading=13, textColor=BRAND_DARK)
    bold    = ParagraphStyle("b", fontName="Helvetica-Bold", fontSize=9, leading=13, textColor=BRAND_DARK)
    small   = ParagraphStyle("s", fontName="Helvetica", fontSize=8, leading=11, textColor=BRAND_GRAY)
    heading = ParagraphStyle("h", fontName="Helvetica-Bold", fontSize=11, leading=16, textColor=BRAND_DARK)
    right   = ParagraphStyle("r", fontName="Helvetica", fontSize=9, alignment=TA_RIGHT, textColor=BRAND_DARK)
    rbold   = ParagraphStyle("rb", fontName="Helvetica-Bold", fontSize=10, alignment=TA_RIGHT, textColor=BRAND_DARK)

    story = []

    # ── Invoice meta ──────────────────────────────────────
    meta_data = [
        [
            Paragraph(f"<b>Invoice #</b> {invoice_data.get('invoice_number', '')}", bold),
            Paragraph(f"<b>Date:</b> {invoice_data.get('date', '')}", normal),
        ],
        [
            Paragraph(f"<b>Job Card:</b> {invoice_data.get('job_number', '')}", normal),
            Paragraph(f"<b>Vehicle:</b> {invoice_data.get('vehicle_plate', '')} — {invoice_data.get('vehicle_name', '')}", normal),
        ],
    ]
    meta_table = Table(meta_data, colWidths=[95 * mm, 85 * mm])
    meta_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BRAND_LIGHT),
        ("BOX", (0, 0), (-1, -1), 0.5, BRAND_LINE),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [BRAND_LIGHT, white]),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 5 * mm))

    # ── Bill to ──────────────────────────────────────────
    story.append(Paragraph("Bill To", ParagraphStyle("bt", fontName="Helvetica-Bold", fontSize=8, textColor=BRAND_GRAY, spaceAfter=2)))
    story.append(Paragraph(invoice_data.get("customer_name", ""), heading))
    if invoice_data.get("customer_phone"):
        story.append(Paragraph(invoice_data["customer_phone"], small))
    if invoice_data.get("customer_address"):
        story.append(Paragraph(invoice_data["customer_address"], small))
    story.append(Spacer(1, 5 * mm))

    # ── Line items ───────────────────────────────────────
    item_headers = ["#", "Description", "Qty", "Unit Price", "Amount"]
    rows = [[Paragraph(h, ParagraphStyle("th", fontName="Helvetica-Bold", fontSize=8, textColor=white)) for h in item_headers]]

    for i, item in enumerate(invoice_data.get("items", []), 1):
        rows.append([
            Paragraph(str(i), normal),
            Paragraph(item.get("description", ""), normal),
            Paragraph(str(item.get("quantity", 1)), normal),
            Paragraph(f"NPR {item.get('unit_price', '0.00')}", right),
            Paragraph(f"NPR {item.get('total', '0.00')}", right),
        ])

    col_widths = [10 * mm, 80 * mm, 18 * mm, 32 * mm, 32 * mm]
    items_table = Table(rows, colWidths=col_widths, repeatRows=1)
    items_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BRAND_DARK),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, BRAND_LIGHT]),
        ("GRID", (0, 0), (-1, -1), 0.3, BRAND_LINE),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 4 * mm))

    # ── Totals ───────────────────────────────────────────
    def money_row(label: str, value: str, bold_row: bool = False, color=None):
        style = rbold if bold_row else right
        val_color = color or BRAND_DARK
        return [
            "",
            Paragraph(label, ParagraphStyle("tl", fontName="Helvetica-Bold" if bold_row else "Helvetica", fontSize=9, textColor=BRAND_GRAY)),
            Paragraph(f"NPR {value}", ParagraphStyle("tv", fontName="Helvetica-Bold" if bold_row else "Helvetica", fontSize=10 if bold_row else 9, alignment=TA_RIGHT, textColor=val_color)),
        ]

    totals_data = [
        money_row("Subtotal", invoice_data.get("subtotal", "0.00")),
    ]
    if float(invoice_data.get("discount_amount", 0)) > 0:
        totals_data.append(money_row(f"Discount ({invoice_data.get('discount_reason', '')})", invoice_data.get("discount_amount", "0.00"), color=SUCCESS))
    totals_data.append(money_row(f"VAT ({invoice_data.get('tax_rate', '13')}%)", invoice_data.get("tax_amount", "0.00")))
    totals_data.append(money_row("TOTAL", invoice_data.get("total_amount", "0.00"), bold_row=True))
    totals_data.append(money_row("Paid", invoice_data.get("paid_amount", "0.00"), color=SUCCESS))

    balance = float(invoice_data.get("total_amount", 0)) - float(invoice_data.get("paid_amount", 0))
    if balance > 0:
        totals_data.append(money_row("Balance Due", f"{balance:.2f}", bold_row=True, color=DANGER))

    totals_table = Table(totals_data, colWidths=[95 * mm, 55 * mm, 32 * mm])
    totals_table.setStyle(TableStyle([
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LINEABOVE", (1, -2 if balance <= 0 else -3), (-1, -2 if balance <= 0 else -3), 0.8, BRAND_DARK),
    ]))
    story.append(totals_table)
    story.append(Spacer(1, 6 * mm))

    # ── Payment status banner ────────────────────────────
    status = invoice_data.get("payment_status", "pending")
    status_color = SUCCESS if status == "paid" else (HexColor("#d97706") if status == "partial" else DANGER)
    story.append(Paragraph(
        f"Payment Status: <b>{status.upper()}</b>" + (f" — via {invoice_data.get('payment_method', '').replace('_', ' ').title()}" if invoice_data.get("payment_method") else ""),
        ParagraphStyle("ps", fontName="Helvetica", fontSize=9, textColor=status_color, borderColor=status_color, borderWidth=0.5, borderPadding=4, leading=14),
    ))

    if invoice_data.get("notes"):
        story.append(Spacer(1, 4 * mm))
        story.append(Paragraph(f"Notes: {invoice_data['notes']}", small))

    doc.build(story, onFirstPage=lambda c, d: _header_canvas(c, d, "TAX INVOICE", invoice_data.get("invoice_number", "")),
              onLaterPages=lambda c, d: _header_canvas(c, d, "TAX INVOICE", invoice_data.get("invoice_number", "")))
    return buf.getvalue()


def generate_gate_pass_pdf(gp_data: dict) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=20 * mm, rightMargin=20 * mm,
                            topMargin=28 * mm, bottomMargin=22 * mm)
    styles = getSampleStyleSheet()
    center  = ParagraphStyle("c", fontName="Helvetica", fontSize=10, alignment=TA_CENTER, textColor=BRAND_DARK, leading=15)
    cbold   = ParagraphStyle("cb", fontName="Helvetica-Bold", fontSize=11, alignment=TA_CENTER, textColor=BRAND_DARK, leading=16)
    small   = ParagraphStyle("s", fontName="Helvetica", fontSize=8, textColor=BRAND_GRAY, leading=11)

    story = []
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph("VEHICLE EXIT GATE PASS", ParagraphStyle("t", fontName="Helvetica-Bold", fontSize=16, alignment=TA_CENTER, textColor=BRAND_DARK, spaceAfter=2)))
    story.append(Paragraph("Present this pass to security before exiting the premises", ParagraphStyle("sub", fontName="Helvetica", fontSize=9, alignment=TA_CENTER, textColor=BRAND_GRAY, spaceAfter=8)))
    story.append(HRFlowable(width="100%", thickness=0.5, color=BRAND_LINE, spaceAfter=6 * mm))

    # QR / verification code box
    story.append(Paragraph("Verification Code", ParagraphStyle("vl", fontName="Helvetica-Bold", fontSize=8, alignment=TA_CENTER, textColor=BRAND_GRAY, spaceAfter=2)))
    code_style = ParagraphStyle("code", fontName="Helvetica-Bold", fontSize=28, alignment=TA_CENTER,
                                textColor=BRAND_DARK, borderColor=BRAND_AMBER, borderWidth=2,
                                borderPadding=10, spaceAfter=4, borderRadius=6, backColor=BRAND_LIGHT)
    story.append(Paragraph(gp_data.get("verification_code", ""), code_style))
    story.append(Spacer(1, 5 * mm))

    # Details table
    details = [
        ["Customer", gp_data.get("customer_name", "")],
        ["Vehicle", f"{gp_data.get('vehicle_plate', '')} — {gp_data.get('vehicle_brand', '')} {gp_data.get('vehicle_model', '')}"],
        ["Job Card #", gp_data.get("job_number", "")],
        ["Invoice #", gp_data.get("invoice_number", "")],
        ["Invoice Total", f"NPR {gp_data.get('total_amount', '0.00')}"],
        ["Payment Status", gp_data.get("payment_status", "").upper()],
        ["Issued On", gp_data.get("issued_at", "")],
    ]

    det_style = ParagraphStyle("d", fontName="Helvetica", fontSize=9, textColor=BRAND_DARK, leading=13)
    det_bold  = ParagraphStyle("db", fontName="Helvetica-Bold", fontSize=9, textColor=BRAND_GRAY, leading=13)

    tbl_data = [[Paragraph(k, det_bold), Paragraph(v, det_style)] for k, v in details]
    tbl = Table(tbl_data, colWidths=[50 * mm, 110 * mm])
    tbl.setStyle(TableStyle([
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [BRAND_LIGHT, white]),
        ("GRID", (0, 0), (-1, -1), 0.3, BRAND_LINE),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 8 * mm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=BRAND_LINE, spaceAfter=4 * mm))
    story.append(Paragraph("Security: Please verify this code and mark as used before allowing exit.", small))
    if gp_data.get("notes"):
        story.append(Paragraph(f"Notes: {gp_data['notes']}", small))

    doc.build(story,
              onFirstPage=lambda c, d: _header_canvas(c, d, "GATE PASS", gp_data.get("verification_code", "")),
              onLaterPages=lambda c, d: _header_canvas(c, d, "GATE PASS", gp_data.get("verification_code", "")))
    return buf.getvalue()


def generate_job_card_pdf(job_data: dict) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=15 * mm, rightMargin=15 * mm,
                            topMargin=28 * mm, bottomMargin=22 * mm)
    normal = ParagraphStyle("n", fontName="Helvetica", fontSize=9, leading=13, textColor=BRAND_DARK)
    bold   = ParagraphStyle("b", fontName="Helvetica-Bold", fontSize=9, leading=13, textColor=BRAND_DARK)
    gray   = ParagraphStyle("g", fontName="Helvetica", fontSize=8, leading=11, textColor=BRAND_GRAY)
    head   = ParagraphStyle("h", fontName="Helvetica-Bold", fontSize=11, leading=16, textColor=BRAND_DARK)

    story = []

    # Meta row
    meta = [
        [Paragraph(f"<b>Job Card #</b> {job_data.get('job_number', '')}", bold),
         Paragraph(f"<b>Status:</b> {job_data.get('status', '').replace('_', ' ').upper()}", bold),
         Paragraph(f"<b>Date:</b> {job_data.get('date', '')}", normal)],
    ]
    mt = Table(meta, colWidths=[65 * mm, 55 * mm, 60 * mm])
    mt.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BRAND_LIGHT),
        ("BOX", (0, 0), (-1, -1), 0.5, BRAND_LINE),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(mt)
    story.append(Spacer(1, 5 * mm))

    # Customer + Vehicle
    cv = [
        [Paragraph("<b>Customer</b>", gray), Paragraph("<b>Vehicle</b>", gray)],
        [Paragraph(job_data.get("customer_name", ""), bold), Paragraph(f"{job_data.get('vehicle_plate', '')} — {job_data.get('vehicle_name', '')}", bold)],
        [Paragraph(job_data.get("customer_phone", ""), normal), Paragraph(f"Odometer In: {job_data.get('odometer_in', 0)} km", normal)],
    ]
    cv_tbl = Table(cv, colWidths=[90 * mm, 90 * mm])
    cv_tbl.setStyle(TableStyle([
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [BRAND_LIGHT, white, white]),
        ("BOX", (0, 0), (-1, -1), 0.5, BRAND_LINE),
        ("LINEAFTER", (0, 0), (0, -1), 0.5, BRAND_LINE),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(cv_tbl)
    story.append(Spacer(1, 5 * mm))

    # Complaint
    story.append(Paragraph("Complaint / Work Required", ParagraphStyle("sec", fontName="Helvetica-Bold", fontSize=8, textColor=BRAND_GRAY, spaceAfter=2)))
    story.append(Paragraph(job_data.get("complaint", "—"), ParagraphStyle("comp", fontName="Helvetica", fontSize=9, textColor=BRAND_DARK, borderColor=BRAND_LINE, borderWidth=0.5, borderPadding=6, leading=14, backColor=BRAND_LIGHT)))
    story.append(Spacer(1, 4 * mm))

    # Diagnosis
    if job_data.get("diagnosis"):
        story.append(Paragraph("Diagnosis", ParagraphStyle("sec2", fontName="Helvetica-Bold", fontSize=8, textColor=BRAND_GRAY, spaceAfter=2)))
        story.append(Paragraph(job_data["diagnosis"], ParagraphStyle("diag", fontName="Helvetica", fontSize=9, textColor=BRAND_DARK, borderColor=BRAND_LINE, borderWidth=0.5, borderPadding=6, leading=14, backColor=BRAND_LIGHT)))
        story.append(Spacer(1, 4 * mm))

    # Financials
    fin = [
        [Paragraph("<b>Estimated Cost</b>", bold), Paragraph(f"NPR {job_data.get('estimated_cost', '0.00')}", ParagraphStyle("fr", fontName="Helvetica", fontSize=9, alignment=TA_RIGHT, textColor=BRAND_DARK))],
        [Paragraph("<b>Labour Charge</b>", bold), Paragraph(f"NPR {job_data.get('labor_charge', '0.00')}", ParagraphStyle("fr", fontName="Helvetica", fontSize=9, alignment=TA_RIGHT, textColor=BRAND_DARK))],
    ]
    fin_tbl = Table(fin, colWidths=[140 * mm, 40 * mm])
    fin_tbl.setStyle(TableStyle([
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [white, BRAND_LIGHT]),
        ("BOX", (0, 0), (-1, -1), 0.5, BRAND_LINE),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(fin_tbl)
    story.append(Spacer(1, 10 * mm))

    # Signatures
    sig_data = [[
        Paragraph("_______________________\nCustomer Signature", ParagraphStyle("sig", fontName="Helvetica", fontSize=8, textColor=BRAND_GRAY, alignment=TA_CENTER, leading=12)),
        Paragraph("_______________________\nMechanic Signature", ParagraphStyle("sig", fontName="Helvetica", fontSize=8, textColor=BRAND_GRAY, alignment=TA_CENTER, leading=12)),
        Paragraph("_______________________\nAuthorized By", ParagraphStyle("sig", fontName="Helvetica", fontSize=8, textColor=BRAND_GRAY, alignment=TA_CENTER, leading=12)),
    ]]
    sig_tbl = Table(sig_data, colWidths=[60 * mm, 60 * mm, 60 * mm])
    sig_tbl.setStyle(TableStyle([("TOPPADDING", (0, 0), (-1, -1), 8)]))
    story.append(sig_tbl)

    doc.build(story,
              onFirstPage=lambda c, d: _header_canvas(c, d, "JOB CARD", job_data.get("job_number", "")),
              onLaterPages=lambda c, d: _header_canvas(c, d, "JOB CARD", job_data.get("job_number", "")))
    return buf.getvalue()