from io import BytesIO
import re
from datetime import datetime
from xml.sax.saxutils import escape

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT


def clean_markdown(text):
    """
    Remove simple Markdown artifacts and normalize characters
    so the PDF output looks cleaner and is less likely to break.
    """
    if not text:
        return ""

    today = datetime.today().strftime("%B %d, %Y")

    text = text.replace("[Date]", today)
    text = text.replace("**", "")
    text = text.replace("###", "")
    text = text.replace("##", "")
    text = text.replace("#", "")
    text = text.replace("---", "")
    text = text.replace("•", "-")
    text = text.replace("–", "-")
    text = text.replace("—", "-")
    text = text.replace("“", '"').replace("”", '"')
    text = text.replace("’", "'")
    text = text.replace("‘", "'")

    return text


def is_section_heading(line):
    """
    Detect common resume / cover letter section headings.
    """
    clean = line.strip().replace(":", "").lower()

    common_headings = {
        "education",
        "technical skills",
        "skills",
        "relevant skills",
        "professional experience",
        "coursework",
        "experience",
        "work experience",
        "related projects",
        "projects",
        "leadership",
        "leadership experience",
        "certifications",
        "professional summary",
        "summary",
        "cover letter",
        "objective",
        "profile",
        "selected projects",
        "academic projects",
        "professional projects",
        "additional experience",
        "awards",
        "activities",
        "volunteer experience",
    }

    return clean in common_headings


def is_bullet(line):
    """
    Detect bullet-style lines.
    """
    clean = line.strip()
    return clean.startswith("- ") or clean.startswith("* ")


def looks_like_contact_line(line):
    """
    Detect contact information line near the top of a resume.
    """
    lower = line.lower()
    return (
        "@" in line
        or "linkedin" in lower
        or "github" in lower
        or "|" in line
        or re.search(r"\d{3}[-.\s]\d{3}[-.\s]\d{4}", line) is not None
    )


def is_cover_letter_text(title, cleaned_text):
    """
    Detect whether the document is likely a cover letter.
    """
    title_lower = title.lower().strip()
    text_lower = cleaned_text.lower()

    return (
        "cover letter" in title_lower
        or "dear " in text_lower
        or "sincerely" in text_lower
    )


def render_cover_letter(lines, story, styles):
    """
    Render cover letter with cleaner business-letter spacing.
    """
    letter_header_style = ParagraphStyle(
        "LetterHeader",
        parent=styles["BodyText"],
        alignment=TA_LEFT,
        fontSize=10.5,
        leading=14,
        spaceAfter=2,
    )

    letter_body_style = ParagraphStyle(
        "LetterBody",
        parent=styles["BodyText"],
        alignment=TA_LEFT,
        fontSize=10.5,
        leading=15,
        spaceAfter=10,
    )

    letter_greeting_style = ParagraphStyle(
        "LetterGreeting",
        parent=styles["BodyText"],
        alignment=TA_LEFT,
        fontSize=10.5,
        leading=15,
        spaceBefore=8,
        spaceAfter=10,
    )

    small_gap = Spacer(1, 0.05 * inch)
    medium_gap = Spacer(1, 0.12 * inch)

    for line in lines:
        clean_line = line.strip()

        if not clean_line:
            story.append(medium_gap)
            continue

        if clean_line in {"-", "--", "---"}:
            continue

        lower_line = clean_line.lower()

        # Greeting
        if lower_line.startswith("dear"):
            story.append(medium_gap)
            story.append(Paragraph(escape(clean_line), letter_greeting_style))

        # Closing
        elif lower_line.startswith("sincerely") or lower_line.startswith("best regards"):
            story.append(medium_gap)
            story.append(Paragraph(escape(clean_line), letter_body_style))

        # Candidate/contact/company block
        elif (
            "@" in clean_line
            or looks_like_contact_line(clean_line)
            or clean_line.startswith("[")
            or len(clean_line.split()) <= 6
        ):
            story.append(Paragraph(escape(clean_line), letter_header_style))

        # Main paragraphs
        else:
            story.append(Paragraph(escape(clean_line), letter_body_style))


def text_to_pdf_bytes(title, body_text):
    """
    Convert plain/markdown-like resume or cover letter text into a cleaner PDF.

    For resumes:
    - If title is empty, the first non-empty line is treated as the resume name header.
    - The second contact-like line is styled as contact information.
    - Section headings and bullets are formatted more cleanly.

    For cover letters:
    - A title such as "Cover Letter" can be provided.
    - [Date] is automatically replaced with today's date.
    - Paragraph spacing is adjusted for a professional letter layout.
    """

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.6 * inch,
        leftMargin=0.6 * inch,
        topMargin=0.55 * inch,
        bottomMargin=0.55 * inch,
    )

    styles = getSampleStyleSheet()

    document_title_style = ParagraphStyle(
        "DocumentTitle",
        parent=styles["Title"],
        alignment=TA_LEFT,
        fontSize=18,
        leading=22,
        spaceAfter=16,
    )

    name_style = ParagraphStyle(
        "ResumeName",
        parent=styles["Title"],
        alignment=TA_LEFT,
        fontSize=17,
        leading=21,
        spaceAfter=6,
    )

    contact_style = ParagraphStyle(
        "ContactInfo",
        parent=styles["BodyText"],
        alignment=TA_LEFT,
        fontSize=9,
        leading=11,
        spaceAfter=10,
    )

    heading_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        alignment=TA_LEFT,
        fontSize=12,
        leading=15,
        spaceBefore=10,
        spaceAfter=5,
    )

    body_style = ParagraphStyle(
        "CustomBody",
        parent=styles["BodyText"],
        fontSize=9.5,
        leading=12.5,
        spaceAfter=4,
    )

    bullet_style = ParagraphStyle(
        "BulletStyle",
        parent=styles["BodyText"],
        fontSize=9.5,
        leading=12.5,
        leftIndent=14,
        firstLineIndent=-8,
        spaceAfter=3,
    )

    small_gap = Spacer(1, 0.05 * inch)
    medium_gap = Spacer(1, 0.10 * inch)

    story = []

    cleaned_text = clean_markdown(body_text)
    raw_lines = cleaned_text.split("\n")
    lines = [line.rstrip() for line in raw_lines]

    # Remove leading empty lines
    while lines and not lines[0].strip():
        lines.pop(0)

    cleaned_title = clean_markdown(title).strip()

    # Cover letter formatting path
    if is_cover_letter_text(cleaned_title, cleaned_text):
        if cleaned_title:
            story.append(Paragraph(escape(cleaned_title), document_title_style))
            story.append(medium_gap)

        render_cover_letter(lines, story, styles)

        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes

    # Resume formatting path
    start_index = 0

    if cleaned_title:
        story.append(Paragraph(escape(cleaned_title), document_title_style))
        story.append(medium_gap)
    else:
        # Resume-style header: first non-empty line = candidate name
        if lines:
            candidate_name = lines[0].strip()
            story.append(Paragraph(f"<b>{escape(candidate_name)}</b>", name_style))
            start_index = 1

        # Optional contact line
        if len(lines) > start_index and looks_like_contact_line(lines[start_index].strip()):
            contact_line = lines[start_index].strip()
            story.append(Paragraph(escape(contact_line), contact_style))
            start_index += 1
        else:
            story.append(small_gap)

    for line in lines[start_index:]:
        clean_line = line.strip()

        if not clean_line:
            story.append(small_gap)
            continue

        # Skip separator remnants
        if clean_line in {"-", "--", "---"}:
            continue

        # Section headings
        if is_section_heading(clean_line):
            story.append(Paragraph(f"<b>{escape(clean_line.upper())}</b>", heading_style))

        # Bullets
        elif is_bullet(clean_line):
            bullet_text = clean_line[2:].strip()
            story.append(Paragraph(f"• {escape(bullet_text)}", bullet_style))

        # Lines that look like all-caps headings even if not in the list
        elif clean_line.isupper() and len(clean_line.split()) <= 4:
            story.append(Paragraph(f"<b>{escape(clean_line)}</b>", heading_style))

        # Normal body text
        else:
            story.append(Paragraph(escape(clean_line), body_style))

    doc.build(story)

    pdf_bytes = buffer.getvalue()
    buffer.close()

    return pdf_bytes