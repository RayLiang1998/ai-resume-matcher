import re
import streamlit as st
from src.file_reader import extract_text_from_file

from src.matcher import compute_match_score
from src.rewriter import (
    check_input_relevance,
    improve_resume,
    explain_improvement,
    suggest_missing_skills,
    generate_cover_letter,
)

from src.exporter import text_to_pdf_bytes


def extract_placeholders(text):
    """
    Extract placeholders like [Your Name], [Company Name], [Date].
    """
    if not text:
        return []

    placeholders = re.findall(r"\[[^\]]+\]", text)
    return sorted(set(placeholders))


def replace_placeholders(text, replacements):
    """
    Replace detected placeholders with user-provided values.
    """
    final_text = text

    for placeholder, value in replacements.items():
        if value and value.strip():
            final_text = final_text.replace(placeholder, value.strip())

    return final_text


st.set_page_config(page_title="AI Resume Matcher & Optimizer", layout="centered")

st.title("AI Resume Matcher & Optimizer")

st.write(
    "This tool compares a resume with a job description, improves the resume safely, "
    "and identifies missing skills without fabricating experience."
)

# Store results so download buttons do not clear the page after clicking
if "results" not in st.session_state:
    st.session_state.results = None


resume = ""
jd = ""

# Resume Input
st.subheader("Resume Input")

resume_file = st.file_uploader(
    "Upload resume file (TXT, PDF, or DOCX)",
    type=["txt", "pdf", "docx"],
    key="resume_file"
)

try:
    resume = extract_text_from_file(resume_file)
    with st.expander("Preview extracted resume text"):
        st.write(resume[:2000] if resume else "No resume text loaded yet.")

except Exception as e:
    st.error(f"File reading error: {e}")

resume_text_input = st.text_area(
    "Or paste your resume here",
    height=180
)

if resume_file is None:
    resume = resume_text_input


# Job Description Input
st.subheader("Job Description Input")

jd_file = st.file_uploader(
    "Upload job description file (TXT, PDF, or DOCX)",
    type=["txt", "pdf", "docx"],
    key="jd_file"
)

try:
    jd = extract_text_from_file(jd_file)
    with st.expander("Preview extracted job description text"):
        st.write(jd[:2000] if jd else "No job description text loaded yet.")

except Exception as e:
    st.error(f"File reading error: {e}")

jd_text_input = st.text_area(
    "Or paste job description here",
    height=180
)

if jd_file is None:
    jd = jd_text_input


if st.button("Analyze & Improve"):
    if not resume or not jd:
        st.warning("Please input both resume and job description.")

    else:
        with st.spinner("Checking input relevance..."):
            validation = check_input_relevance(resume, jd)

        if not validation["is_valid"]:
            st.session_state.results = None

            error_lines = [
                "Invalid input detected. This tool only supports resume/profile input "
                "and job-description alignment tasks.",
                ""
            ]

            if validation["resume_status"] == "INVALID":
                error_lines.append("**Resume status: INVALID**")

            if validation["jd_status"] == "INVALID":
                error_lines.append("**Job Description status: INVALID**")

            error_lines.append(f"**Reason:** {validation['reason']}")

            st.error("  \n".join(error_lines))

        else:
            with st.spinner("Analyzing and improving resume..."):
                original_score = compute_match_score(resume, jd)

                improved_resume = improve_resume(resume, jd)
                improved_score = compute_match_score(improved_resume, jd)

                improvements = explain_improvement(resume, improved_resume, jd)
                missing_suggestions = suggest_missing_skills(resume, jd)
                cover_letter = generate_cover_letter(resume, jd)

            # Store raw generated results.
            # PDF files will be generated later after placeholder replacement.
            st.session_state.results = {
                "original_score": original_score,
                "improved_score": improved_score,
                "improved_resume": improved_resume,
                "improvements": improvements,
                "missing_suggestions": missing_suggestions,
                "cover_letter": cover_letter,
            }


# Display stored results outside the button block
if st.session_state.results:
    results = st.session_state.results

    original_score = results["original_score"]
    improved_score = results["improved_score"]
    improved_resume = results["improved_resume"]
    improvements = results["improvements"]
    missing_suggestions = results["missing_suggestions"]
    cover_letter = results["cover_letter"]

    st.subheader("Match Score Comparison")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Original Score", f"{original_score}/100")

    with col2:
        st.metric("Improved Score", f"{improved_score}/100")

    with col3:
        st.metric("Score Increase", f"{round(improved_score - original_score, 2)}")

    st.caption(
        "Note: This score is an internal keyword-based alignment score, "
        "not an official ATS score."
    )

    st.subheader("Improved Resume")
    st.write(improved_resume)

    st.subheader("Generated Cover Letter")
    st.write(cover_letter)

    # =========================
    # Shared Placeholder Section
    # =========================

    all_placeholders = sorted(
        set(extract_placeholders(improved_resume) + extract_placeholders(cover_letter))
    )

    shared_replacements = {}

    if all_placeholders:
        st.subheader("Missing Information Required")
        st.write(
            "Some placeholders were detected in the generated resume and/or cover letter. "
            "Please provide the missing information below. Each value will be applied to both documents."
        )

        for idx, placeholder in enumerate(all_placeholders):
            clean_label = placeholder.replace("[", "").replace("]", "").strip()
            safe_key = re.sub(r"[^a-zA-Z0-9_]", "_", clean_label)

            shared_replacements[placeholder] = st.text_input(
                f"Enter value for {clean_label}",
                key=f"shared_placeholder_{idx}_{safe_key}"
            )

    final_resume = replace_placeholders(improved_resume, shared_replacements)
    final_cover_letter = replace_placeholders(cover_letter, shared_replacements)

    if all_placeholders:
        with st.expander("Preview final resume after placeholder replacement"):
            st.write(final_resume)

        with st.expander("Preview final cover letter after placeholder replacement"):
            st.write(final_cover_letter)

    st.subheader("Improvements Detected")
    st.write(improvements)

    st.subheader("Missing Skills / Development Suggestions")
    st.write(missing_suggestions)

    st.caption(
        "Important: Missing skills should be learned or gained through real experience. "
        "The system should not add unsupported qualifications to the resume."
    )

    # Generate PDF files after placeholder replacement
    improved_resume_pdf = text_to_pdf_bytes(
        "",
        final_resume
    )

    cover_letter_pdf = text_to_pdf_bytes(
        "Cover Letter",
        final_cover_letter
    )

    st.subheader("Download Outputs")

    st.download_button(
        label="Download Improved Resume as TXT",
        data=final_resume,
        file_name="improved_resume.txt",
        mime="text/plain",
        key="download_resume_txt",
    )

    st.download_button(
        label="Download Cover Letter as TXT",
        data=final_cover_letter,
        file_name="cover_letter.txt",
        mime="text/plain",
        key="download_cover_txt",
    )

    st.download_button(
        label="Download Improved Resume as PDF",
        data=improved_resume_pdf,
        file_name="improved_resume.pdf",
        mime="application/pdf",
        key="download_resume_pdf",
    )

    st.download_button(
        label="Download Cover Letter as PDF",
        data=cover_letter_pdf,
        file_name="cover_letter.pdf",
        mime="application/pdf",
        key="download_cover_pdf",
    )