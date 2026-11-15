import os
from pathlib import Path
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, HRFlowable, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

def create_credentials_pdf(output_path: str):
    # Setup document
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=32,
        bottomMargin=32
    )

    styles = getSampleStyleSheet()

    # Color Palette - MNC Enterprise Tech Blue & Slate
    PRIMARY = colors.HexColor("#0f172a")     # Deep Slate
    ACCENT_BLUE = colors.HexColor("#1e40af") # Corporate Royal Blue
    ACCENT_CYAN = colors.HexColor("#0284c7") # Electric Cyan
    AMBER = colors.HexColor("#b45309")       # Warning Amber
    DARK_BG = colors.HexColor("#f8fafc")     # Light Crisp Slate
    CARD_BG = colors.HexColor("#ffffff")
    BORDER_COLOR = colors.HexColor("#cbd5e1")
    TEXT_MAIN = colors.HexColor("#0f172a")
    TEXT_MUTED = colors.HexColor("#475569")
    SUCCESS_GREEN = colors.HexColor("#15803d")

    # Typography styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=15,
        leading=18,
        textColor=PRIMARY,
        alignment=0
    )
    
    sub_title_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        textColor=TEXT_MUTED,
        alignment=0
    )

    confidential_badge = ParagraphStyle(
        'ConfBadge',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#991b1b"),
        alignment=2
    )

    section_header_style = ParagraphStyle(
        'SecHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        textColor=ACCENT_BLUE,
        spaceAfter=4
    )

    cell_bold = ParagraphStyle(
        'CellBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=PRIMARY
    )

    cell_normal = ParagraphStyle(
        'CellNormal',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10.5,
        textColor=TEXT_MAIN
    )

    cell_mono = ParagraphStyle(
        'CellMono',
        parent=styles['Normal'],
        fontName='Courier-Bold',
        fontSize=8.5,
        leading=11,
        textColor=ACCENT_BLUE
    )

    cell_pw = ParagraphStyle(
        'CellPW',
        parent=styles['Normal'],
        fontName='Courier-Bold',
        fontSize=9,
        leading=11,
        textColor=colors.HexColor("#b91c1c")
    )

    note_style = ParagraphStyle(
        'NoteStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        leading=10,
        textColor=TEXT_MUTED
    )

    elements = []

    # Paths to assets
    base_dir = Path(__file__).resolve().parent
    hari_logo_path = base_dir / "public" / "hari-university-logo.png"
    technoverse_logo_path = base_dir / "public" / "logo-full.png"

    # Header Section with Logos and Title
    # Column 1: Technoverse Logo | Column 2: Titles | Column 3: Hari University Logo
    hari_img = Image(str(hari_logo_path), width=52, height=50) if hari_logo_path.exists() else Paragraph("HARI UNIV", cell_bold)
    tech_img = Image(str(technoverse_logo_path), width=130, height=36) if technoverse_logo_path.exists() else Paragraph("TECHNOVERSE", cell_bold)

    title_block = [
        Paragraph("<b>HARI UNIVERSITY</b>", ParagraphStyle('HUniv', fontName='Helvetica-Bold', fontSize=12, leading=14, textColor=PRIMARY)),
        Paragraph("DEPARTMENT OF STUDENT AFFAIRS & TECHNICAL SOCIETIES", ParagraphStyle('Dept', fontName='Helvetica-Bold', fontSize=7.5, leading=9, textColor=ACCENT_BLUE)),
        Paragraph("TECHNOVERSE CLUB • OFFICIAL EXECUTIVE PORTAL", ParagraphStyle('TechClub', fontName='Helvetica', fontSize=8, leading=10, textColor=TEXT_MUTED)),
    ]

    header_data = [
        [tech_img, title_block, hari_img]
    ]
    header_table = Table(header_data, colWidths=[140, 310, 70])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (0,0), (0,0), 'LEFT'),
        ('ALIGN', (1,0), (1,0), 'CENTER'),
        ('ALIGN', (2,0), (2,0), 'RIGHT'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
    ]))
    elements.append(header_table)

    elements.append(Spacer(1, 8))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=ACCENT_BLUE, spaceBefore=2, spaceAfter=8))

    # Meta bar
    meta_data = [
        [
            Paragraph("<b>DOCUMENT:</b> TC-EXEC-AUTH-2026/01", cell_normal),
            Paragraph(f"<b>DATE:</b> {datetime.now().strftime('%B %d, %Y')}", cell_normal),
            Paragraph("<b>CLASSIFICATION:</b> <font color='#dc2626'>STRICTLY CONFIDENTIAL</font>", cell_normal),
            Paragraph("<b>PORTAL:</b> http://localhost:5001", cell_normal),
        ]
    ]
    meta_table = Table(meta_data, colWidths=[140, 100, 150, 130])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f1f5f9")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    elements.append(meta_table)

    elements.append(Spacer(1, 10))

    # Heading: TOP 4 COMMITTEE ROLES
    elements.append(Paragraph("OFFICIAL CREDENTIALS: TOP 4 COMMITTEE EXECUTIVE ROLES", section_header_style))
    elements.append(Paragraph("Constituted as per the official University circular. Authorized for primary executive administration, portal governance, and financial authorizations.", sub_title_style))
    elements.append(Spacer(1, 6))

    # Table of Top 4 Roles
    top_4_headers = [
        Paragraph("<b>S.No</b>", cell_bold),
        Paragraph("<b>Designation</b>", cell_bold),
        Paragraph("<b>Appointed Member</b>", cell_bold),
        Paragraph("<b>Branch</b>", cell_bold),
        Paragraph("<b>User ID (Roll No)</b>", cell_bold),
        Paragraph("<b>Access Password</b>", cell_bold),
        Paragraph("<b>Assigned System Scope</b>", cell_bold),
    ]

    top_4_rows = [
        [
            Paragraph("1", cell_bold),
            Paragraph("<b>President</b><br/><font color='#1e40af' size='6.5'>Chief Executive</font>", cell_normal),
            Paragraph("<b>Karthik</b>", cell_bold),
            Paragraph("CSE-1<br/><font size='6.5' color='#64748b'>1st Year B.Tech</font>", cell_normal),
            Paragraph("26ET103047", cell_mono),
            Paragraph("9032936677", cell_pw),
            Paragraph("Full club governance, account provisioning, task dispatch, budget authorizations", cell_normal),
        ],
        [
            Paragraph("2", cell_bold),
            Paragraph("<b>Vice President</b><br/><font color='#1e40af' size='6.5'>Executive Deputy</font>", cell_normal),
            Paragraph("<b>D. Yakshagna</b>", cell_bold),
            Paragraph("CSM-3<br/><font size='6.5' color='#64748b'>1st Year B.Tech</font>", cell_normal),
            Paragraph("26ET104152", cell_mono),
            Paragraph("9894474159", cell_pw),
            Paragraph("Operations oversight, event execution, minutes verification, lead meetings", cell_normal),
        ],
        [
            Paragraph("3", cell_bold),
            Paragraph("<b>Secretary</b><br/><font color='#1e40af' size='6.5'>Administration</font>", cell_normal),
            Paragraph("<b>B. Sariyu</b>", cell_bold),
            Paragraph("CSD<br/><font size='6.5' color='#64748b'>1st Year B.Tech</font>", cell_normal),
            Paragraph("26ET102005", cell_mono),
            Paragraph("8519802425", cell_pw),
            Paragraph("Official meeting minutes (MoM), action items conversion, attendance records", cell_normal),
        ],
        [
            Paragraph("4", cell_bold),
            Paragraph("<b>Treasurer</b><br/><font color='#1e40af' size='6.5'>Chief Financial Officer</font>", cell_normal),
            Paragraph("<b>Chaitanya</b>", cell_bold),
            Paragraph("CSM-1<br/><font size='6.5' color='#64748b'>1st Year B.Tech</font>", cell_normal),
            Paragraph("26ET104048", cell_mono),
            Paragraph("8639638181", cell_pw),
            Paragraph("Ledger maintenance, ₹ expense approvals, sponsorship receipts, audit logs", cell_normal),
        ],
    ]

    table_data = [top_4_headers] + top_4_rows
    # Available width: A4 (595.27) - 72 = 523.27
    col_widths = [26, 85, 80, 52, 78, 76, 126]
    top_4_table = Table(table_data, colWidths=col_widths, repeatRows=1)
    top_4_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0f172a")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (0,-1), 'CENTER'),
        ('ALIGN', (1,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#0f172a")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#f8fafc")]),
        ('TOPPADDING', (0,0), (-1,-1), 4.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4.5),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(top_4_table)

    elements.append(Spacer(1, 10))

    # FACULTY & ADMINISTRATIVE AUTHORITY SECTION
    elements.append(Paragraph("FACULTY & ADMINISTRATIVE OVERSIGHT", section_header_style))
    elements.append(Paragraph("Holds supervisory control and master account creation authorization alongside the President.", sub_title_style))
    elements.append(Spacer(1, 5))

    coord_headers = [
        Paragraph("<b>Designation</b>", cell_bold),
        Paragraph("<b>Officer / Faculty</b>", cell_bold),
        Paragraph("<b>Department</b>", cell_bold),
        Paragraph("<b>User ID (Staff Code)</b>", cell_bold),
        Paragraph("<b>Access Password</b>", cell_bold),
        Paragraph("<b>System Administrative Authority</b>", cell_bold),
    ]

    coord_row = [
        Paragraph("<b>Club Coordinator</b><br/><font color='#b45309' size='6.5'>Faculty Head</font>", cell_normal),
        Paragraph("<b>Chandini.B</b>", cell_bold),
        Paragraph("CSE<br/><font size='6.5' color='#64748b'>Faculty Advisor</font>", cell_normal),
        Paragraph("COORD01", cell_mono),
        Paragraph("coordinator123", cell_pw),
        Paragraph("Master administrative rights, member provisioning (/team), database settings & global parameters", cell_normal),
    ]

    coord_table = Table([coord_headers, coord_row], colWidths=[90, 80, 60, 86, 81, 126])
    coord_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1e293b")),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#1e293b")),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor("#fffbeb")),
        ('TOPPADDING', (0,0), (-1,-1), 4.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4.5),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(coord_table)

    elements.append(Spacer(1, 10))

    # SYSTEM GUIDELINES & PROTOCOLS
    elements.append(Paragraph("SECURITY PROTOCOLS & INSTRUCTIONS", section_header_style))
    
    protocols_data = [
        [
            Paragraph("<b>1. Authentication Endpoint:</b><br/>Sign in via <code>http://localhost:5001/login</code> using your assigned Roll Number / User ID and initial password.", note_style),
            Paragraph("<b>2. Restricted Account Creation:</b><br/>Public registration is strictly deactivated. Only the <b>Club Coordinator (Chandini.B)</b> and <b>President (Karthik)</b> can provision accounts via <code>/team</code>.", note_style)
        ],
        [
            Paragraph("<b>3. First-Time Login Action:</b><br/>Executives are advised to navigate to <b>Settings (/settings)</b> immediately upon first sign-in to personalize their access credentials.", note_style),
            Paragraph("<b>4. Non-Transferable Access:</b><br/>These credentials grant direct elevated database permissions. Under no circumstances should these details be shared or posted publicly.", note_style)
        ]
    ]
    protocols_table = Table(protocols_data, colWidths=[260, 260])
    protocols_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    elements.append(protocols_table)

    elements.append(Spacer(1, 12))

    # Signatures Table
    sig_data = [
        [
            Paragraph("____________________________<br/><b>Karthik</b><br/>President, Technoverse Club", ParagraphStyle('Sig1', fontName='Helvetica', fontSize=7.5, leading=10, alignment=1)),
            Paragraph("____________________________<br/><b>Chandini.B</b><br/>Club Coordinator, Technoverse", ParagraphStyle('Sig2', fontName='Helvetica', fontSize=7.5, leading=10, alignment=1)),
            Paragraph("____________________________<br/><b>Office of Student Affairs</b><br/>Hari University Official Seal", ParagraphStyle('Sig3', fontName='Helvetica', fontSize=7.5, leading=10, alignment=1)),
        ]
    ]
    sig_table = Table(sig_data, colWidths=[174, 174, 174])
    sig_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'BOTTOM'),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
    ]))
    elements.append(sig_table)

    elements.append(Spacer(1, 10))
    elements.append(HRFlowable(width="100%", thickness=0.75, color=colors.HexColor("#cbd5e1"), spaceBefore=2, spaceAfter=4))
    elements.append(Paragraph(
        "Built by Technoverse. All rights reserved. • Technoverse Club • Official Technical Body of Hari University • Strictly Confidential",
        ParagraphStyle('Footer', fontName='Helvetica', fontSize=6.5, leading=8, textColor=colors.HexColor("#94a3b8"), alignment=1)
    ))

    # Build PDF
    doc.build(elements)
    print(f"✓ PDF successfully generated at: {output_path}")

if __name__ == "__main__":
    out_file = Path(__file__).resolve().parent / "public" / "Technoverse_Top_Roles_Credentials.pdf"
    create_credentials_pdf(str(out_file))
