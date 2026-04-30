from pypdf import PdfReader
from docx import Document


def read_txt(uploaded_file):
    return uploaded_file.read().decode("utf-8", errors="ignore")


def read_pdf(uploaded_file):
    reader = PdfReader(uploaded_file)
    text = ""

    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"

    return text.strip()


def read_docx(uploaded_file):
    document = Document(uploaded_file)
    text_parts = []

    for paragraph in document.paragraphs:
        if paragraph.text.strip():
            text_parts.append(paragraph.text)

    return "\n".join(text_parts).strip()


def extract_text_from_file(uploaded_file):
    if uploaded_file is None:
        return ""

    file_name = uploaded_file.name.lower()

    if file_name.endswith(".txt"):
        return read_txt(uploaded_file)

    elif file_name.endswith(".pdf"):
        return read_pdf(uploaded_file)

    elif file_name.endswith(".docx"):
        return read_docx(uploaded_file)

    else:
        raise ValueError("Unsupported file type. Please upload a TXT, PDF, or DOCX file.")