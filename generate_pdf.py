import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_header_footer(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_header_footer(self, page_count):
        self.saveState()
        self.setFont("Helvetica-Bold", 8.5)
        self.setFillColor(colors.HexColor("#475569"))
        self.drawString(54, 752, "CARBON CRUNCH  |  Shortlisting Assignment Documentation")
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.75)
        self.line(54, 744, 558, 744)

        self.line(54, 40, 558, 40)
        self.setFont("Helvetica", 8.5)
        self.drawString(54, 28, "Prepared by: Atharva Tiwari")
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(558, 28, page_text)
        self.restoreState()

def create_documentation_pdf(filename="Atharva_Tiwari_Carbon_Crunch_Documentation.pdf"):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=50
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#0F172A"),
        spaceAfter=2
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#475569"),
        spaceAfter=8
    )

    h1_style = ParagraphStyle(
        'Heading1_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11.5,
        leading=15,
        textColor=colors.HexColor("#1E293B"),
        spaceBefore=8,
        spaceAfter=4
    )

    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#334155"),
        spaceAfter=4
    )

    bullet_style = ParagraphStyle(
        'Bullet_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#334155"),
        leftIndent=12,
        spaceAfter=3
    )

    story = []

    story.append(Paragraph("Receipt Information Extraction System", title_style))
    story.append(Paragraph("Project Documentation & Technical Summary", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#E2E8F0"), spaceAfter=6))

    story.append(Paragraph("1. Project Goal & Overview", h1_style))
    story.append(Paragraph(
        "The objective of this project is to build an automated software system that reads images of paper receipts and extracts structured information from them. Receipt images in the real world come with many difficulties, such as slanted camera angles, faint thermal paper printouts, shadows, and inconsistent layouts.",
        body_style
    ))
    story.append(Paragraph(
        "The system processes receipt images, extracts text using Optical Character Recognition (OCR), finds important fields like store name, transaction date, line items with prices, and grand total, assigns a confidence reliability score to each field, and calculates an overall financial expense summary across all receipts.",
        body_style
    ))

    story.append(Paragraph("2. Step-by-Step Approach", h1_style))
    story.append(Paragraph("The system follows a simple 5-step pipeline:", body_style))

    story.append(Paragraph("• <b>Step 1: Image Preprocessing</b> – Cleans raw receipt images before reading text. Automatically detects tilt and straightens the image (deskewing), calculates image focus sharpness to spot blur, smooths background noise using Gaussian blur, and enhances text contrast using CLAHE (Contrast Limited Adaptive Histogram Equalization).", bullet_style))
    story.append(Paragraph("• <b>Step 2: Text Detection & Recognition</b> – Uses EasyOCR (a deep learning OCR engine based on CRAFT text detection and ResNet CRNN neural networks) to detect all text regions and convert images into readable words with individual confidence scores.", bullet_style))
    story.append(Paragraph("• <b>Step 3: Line Grouping</b> – Groups scattered text boxes sharing the same horizontal row into clean physical reading lines, preserving left-to-right word order.", bullet_style))
    story.append(Paragraph("• <b>Step 4: Field Extraction</b> – Uses simple rules and pattern matching to identify key information:", bullet_style))
    story.append(Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;- <b>Store Name:</b> Looks at top header text and matches against known retail store names (Walmart, Target, Costco, etc.).", bullet_style))
    story.append(Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;- <b>Transaction Date:</b> Scans text for standard date formats (YYYY-MM-DD, MM/DD/YYYY, DD MMM YYYY) using regular expressions.", bullet_style))
    story.append(Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;- <b>Line Items & Prices:</b> Scans the middle receipt section to pair item descriptions with their respective prices.", bullet_style))
    story.append(Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;- <b>Total Amount:</b> Finds key summary words like 'TOTAL', 'GRAND TOTAL', or 'BALANCE DUE' and reads the corresponding price.", bullet_style))
    story.append(Paragraph("• <b>Step 5: Confidence Scoring & Financial Summary</b> – Assigns a score (0.0 to 1.0) to every field based on OCR quality, format validity, and mathematical consistency (verifying if item prices add up close to the total). Summarizes total money spent across all receipts, transaction counts, and store breakdowns.", bullet_style))

    story.append(Spacer(1, 4))
    story.append(Paragraph("3. Tools & Technologies Used", h1_style))

    tool_data = [
        [Paragraph("<b>Category</b>", body_style), Paragraph("<b>Tool / Library</b>", body_style), Paragraph("<b>What it is used for</b>", body_style)],
        [Paragraph("Language", body_style), Paragraph("Python 3.13", body_style), Paragraph("Main programming language used to write the pipeline.", body_style)],
        [Paragraph("Computer Vision", body_style), Paragraph("OpenCV & Pillow", body_style), Paragraph("Image resizing, deskewing, contrast adjustment, and drawing bounding boxes.", body_style)],
        [Paragraph("OCR Engine", body_style), Paragraph("EasyOCR (PyTorch)", body_style), Paragraph("Deep-learning engine to find text regions and convert images to text.", body_style)],
        [Paragraph("Data Processing", body_style), Paragraph("NumPy & Pandas", body_style), Paragraph("Math operations, bounding box spatial calculations, and tabular data.", body_style)],
        [Paragraph("User Interface", body_style), Paragraph("Streamlit", body_style), Paragraph("Interactive web dashboard to view receipts, text overlays, and charts.", body_style)],
        [Paragraph("Testing", body_style), Paragraph("Pytest", body_style), Paragraph("Automated test suite to verify pipeline accuracy.", body_style)]
    ]

    t = Table(tool_data, colWidths=[90, 105, 309])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#F1F5F9")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor("#0F172A")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
    ]))
    story.append(t)

    story.append(Spacer(1, 6))
    story.append(Paragraph("4. Real-World Challenges & How They Were Solved", h1_style))

    story.append(Paragraph("<b>Challenge 1: Rotated or Angled Receipts</b>", body_style))
    story.append(Paragraph("• <i>Problem:</i> People often take receipt photos at an angle, making text tilted.", bullet_style))
    story.append(Paragraph("• <i>Solution:</i> Used OpenCV line detection (Hough Lines) to calculate the rotation angle and automatically rotate the image back to horizontal.", bullet_style))

    story.append(Paragraph("<b>Challenge 2: Jumbled OCR Text Output</b>", body_style))
    story.append(Paragraph("• <i>Problem:</i> Standard OCR outputs words out of order across the page.", bullet_style))
    story.append(Paragraph("• <i>Solution:</i> Created a spatial line-grouping algorithm that calculates text box heights and groups words sharing the same row from left to right.", bullet_style))

    story.append(Paragraph("<b>Challenge 3: Distinguishing Grand Total from Subtotal & Tax</b>", body_style))
    story.append(Paragraph("• <i>Problem:</i> Receipts show multiple amounts like Subtotal, Tax, Cash Tendered, and Total.", bullet_style))
    story.append(Paragraph("• <i>Solution:</i> Priority keyword matching for 'GRAND TOTAL' / 'BALANCE DUE', searching lower image sections, and cross-checking against item price sums.", bullet_style))

    story.append(Paragraph("<b>Challenge 4: Faint Printouts on Thermal Paper</b>", body_style))
    story.append(Paragraph("• <i>Problem:</i> Thermal receipt paper fades over time or has bad lighting.", bullet_style))
    story.append(Paragraph("• <i>Solution:</i> Applied Contrast Limited Adaptive Histogram Equalization (CLAHE) to boost character visibility against bright backgrounds.", bullet_style))

    story.append(Spacer(1, 4))
    story.append(Paragraph("5. Future Improvements", h1_style))
    story.append(Paragraph("• <b>Multimodal Model Fallback:</b> Add vision-language models (such as LayoutLM or Donut) as a backup for unusual receipt designs.", bullet_style))
    story.append(Paragraph("• <b>User Editing Interface:</b> Allow users to edit low-confidence fields directly in the Streamlit web dashboard.", bullet_style))
    story.append(Paragraph("• <b>Automatic Multi-Currency Support:</b> Expand regex patterns to automatically parse international currencies ($, EUR, GBP, INR, JPY).", bullet_style))
    story.append(Paragraph("• <b>Receipt Category Tagging:</b> Automatically classify expenses into categories (Groceries, Dining, Hardware, Electronics).", bullet_style))

    story.append(Spacer(1, 6))

    summary_box = [
        [Paragraph("<b>Project Deliverables Summary Checklist</b>", body_style)],
        [Paragraph("✓ Preprocessing pipeline for noise, blur, skew, and contrast normalization", bullet_style)],
        [Paragraph("✓ EasyOCR text detection & recognition with spatial line reconstruction", bullet_style)],
        [Paragraph("✓ Extraction logic for Store Name, Date, Line Items, Prices, and Total Amount", bullet_style)],
        [Paragraph("✓ Multi-factor confidence scoring (0.0 to 1.0) and reliability flags (<0.70)", bullet_style)],
        [Paragraph("✓ Financial summary generation (Total spend, transaction count, itemized purchase breakdown)", bullet_style)],
        [Paragraph("✓ Interactive Streamlit web app dashboard & automated Pytest unit tests (6/6 passed)", bullet_style)]
    ]
    sb_table = Table(summary_box, colWidths=[504])
    sb_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
        ('BOX', (0, 0), (-1, -1), 0.75, colors.HexColor("#CBD5E1")),
        ('PADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(sb_table)

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"PDF documentation successfully created: {filename}")

if __name__ == "__main__":
    create_documentation_pdf()
