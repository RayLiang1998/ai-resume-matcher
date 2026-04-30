from openai import OpenAI
from dotenv import load_dotenv
import re
from datetime import datetime
import os

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def check_input_relevance(resume, jd):
    prompt = f"""
You are an input validation assistant for a resume-job matching tool.

Your ONLY task is to validate each input independently.

Do NOT judge whether the candidate background matches the job description.
A customer service resume and a software engineering job description should still be VALID
as long as the first input is a candidate background and the second input is a job description.

Validate Input 1:
It is VALID if it contains any meaningful candidate, resume, profile, or professional background information.
Examples of valid candidate background:
- work experience
- job title
- skills
- education
- projects
- professional summary
- career history
- volunteer experience
- internship experience

Validate Input 2:
It is VALID if it contains any meaningful job, role, hiring, or position information.
Examples of valid job description:
- job title
- required skills
- responsibilities
- qualifications
- role expectations
- hiring requirements

Mark an input INVALID only if it is clearly unrelated, empty, meaningless, or not usable as that input type.

Important:
- Do NOT compare the resume against the job description.
- Do NOT reject because the candidate is underqualified.
- Do NOT reject because the candidate is from a different field.
- Different career fields are allowed.

Candidate Background Input:
{resume}

Job / Role Description Input:
{jd}

Return your answer in this exact format:
RESUME_STATUS: VALID or INVALID
JD_STATUS: VALID or INVALID
REASON: one short sentence explaining only input validity, not job fit
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    result = response.choices[0].message.content.strip()

    resume_status = "UNKNOWN"
    jd_status = "UNKNOWN"
    reason = "Validation failed."

    for line in result.splitlines():
        line = line.strip()

        if line.startswith("RESUME_STATUS:"):
            resume_status = line.replace("RESUME_STATUS:", "").strip().upper()

        elif line.startswith("JD_STATUS:"):
            jd_status = line.replace("JD_STATUS:", "").strip().upper()

        elif line.startswith("REASON:"):
            reason = line.replace("REASON:", "").strip()

    is_valid = resume_status == "VALID" and jd_status == "VALID"

    return {
        "is_valid": is_valid,
        "resume_status": resume_status,
        "jd_status": jd_status,
        "reason": reason,
        "raw_result": result
    }


# -----------------------------
# Helper Functions
# -----------------------------

def extract_candidate_name(resume):
    lines = [line.strip() for line in resume.splitlines() if line.strip()]

    for line in lines:
        lower = line.lower()

        if "@" in line:
            continue
        if "linkedin" in lower or "github" in lower:
            continue
        if re.search(r"\d{3}[-.\s]\d{3}[-.\s]\d{4}", line):
            continue
        if "|" in line:
            continue
        if len(line.split()) > 6:
            continue

        return line

    return None


def extract_hiring_manager_name(jd):
    patterns = [
        r"hiring manager\s*:\s*(.+)",
        r"recruiter\s*:\s*(.+)",
        r"contact person\s*:\s*(.+)",
        r"manager\s*:\s*(.+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, jd, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            if name:
                return name

    return None


def extract_company_name(jd):
    patterns = [
        r"company\s*:\s*(.+)",
        r"company name\s*:\s*(.+)",
        r"employer\s*:\s*(.+)",
        r"organization\s*:\s*(.+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, jd, re.IGNORECASE)
        if match:
            company = match.group(1).strip()
            if company:
                return company

    return None


def extract_company_address_lines(jd):
    """
    Extract company address from JD if it appears after labels like:
    Company Address: 125 Innovation Drive, Boston, MA 02110
    Address: 125 Innovation Drive, Boston, MA 02110
    """
    patterns = [
        r"company address\s*:\s*(.+)",
        r"address\s*:\s*(.+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, jd, re.IGNORECASE)
        if match:
            address = match.group(1).strip()

            # Split "Address, City, State, ZIP"
            # into:
            # Address
            # City, State, ZIP
            parts = [part.strip() for part in address.split(",")]

            if len(parts) >= 3:
                street = parts[0]
                city_state_zip = ", ".join(parts[1:])
                return street, city_state_zip

            return address, None

    return None, None


def has_real_street_address(text):
    return bool(re.search(r"\d{2,6}\s+[A-Za-z0-9 .'-]+", text))


def has_real_city_state_zip(text):
    return bool(re.search(r"[A-Za-z .'-]+,\s*[A-Z]{2}\s*\d{5}", text))


def has_real_company_name(text):
    return bool(
        re.search(
            r"(Inc\.?|LLC|Corporation|Corp\.?|Company|Technologies|Technology|Solutions|Systems|Group|Labs|Studio|Media|University)",
            text,
            re.IGNORECASE
        )
    )


def ensure_employer_block(final_text, resume, jd):
    """
    Ensure the cover letter has a complete employer block after the date.
    If actual information exists, do not duplicate placeholders.
    If information is missing, insert placeholders.
    """
    today = datetime.today().strftime("%B %d, %Y")

    hiring_manager = extract_hiring_manager_name(jd)
    company_name = extract_company_name(jd)
    street_address, city_state_zip = extract_company_address_lines(jd)

    lines = final_text.splitlines()
    existing_text = "\n".join(lines)

    # Detect what already exists in the generated cover letter
    has_manager = bool(hiring_manager and hiring_manager in existing_text)
    has_company = bool(company_name and company_name in existing_text) or has_real_company_name(existing_text)
    has_street = bool(street_address and street_address in existing_text) or has_real_street_address(existing_text)
    has_city_state_zip = bool(city_state_zip and city_state_zip in existing_text) or has_real_city_state_zip(existing_text)

    manager_line = hiring_manager if hiring_manager else "[Hiring Manager's Name]"
    company_line = company_name if company_name else "[Company Name]"
    street_line = street_address if street_address else "[Company Address]"
    city_line = city_state_zip if city_state_zip else "[City, State, ZIP]"

    # Remove accidental combined placeholder line like:
    # [Company Address] [City, State, ZIP]
    final_text = re.sub(
        r"^\[Company Address\]\s+\[City,\s*State,\s*ZIP\]$",
        "",
        final_text,
        flags=re.MULTILINE
    )

    lines = final_text.splitlines()
    existing_text = "\n".join(lines)

    # Re-check after cleanup
    has_manager = bool(hiring_manager and hiring_manager in existing_text)
    has_company = bool(company_name and company_name in existing_text) or has_real_company_name(existing_text)
    has_street = bool(street_address and street_address in existing_text) or has_real_street_address(existing_text)
    has_city_state_zip = bool(city_state_zip and city_state_zip in existing_text) or has_real_city_state_zip(existing_text)

    missing_block_lines = []

    if not has_manager and "[Hiring Manager's Name]" not in existing_text:
        missing_block_lines.append(manager_line)

    if not has_company and "[Company Name]" not in existing_text:
        missing_block_lines.append(company_line)

    if not has_street and "[Company Address]" not in existing_text:
        missing_block_lines.append(street_line)

    if not has_city_state_zip and "[City, State, ZIP]" not in existing_text:
        missing_block_lines.append(city_line)

    if not missing_block_lines:
        return final_text

    new_lines = []
    inserted = False

    for line in lines:
        new_lines.append(line)

        # Insert missing employer information after the date
        if not inserted and today in line:
            new_lines.append("")
            for item in missing_block_lines:
                new_lines.append(item)
            inserted = True

    if not inserted:
        # Fallback: insert near the top if date somehow cannot be found
        new_lines = missing_block_lines + [""] + new_lines

    return "\n".join(new_lines)


def normalize_greeting(final_text):
    """
    Ensure greeting starts with Dear.
    """
    final_text = re.sub(
        r"^\[Hiring Manager's Name\],$",
        "Dear [Hiring Manager's Name],",
        final_text,
        flags=re.MULTILINE
    )

    final_text = re.sub(
        r"^\[Hiring Manager's Name\]:$",
        "Dear [Hiring Manager's Name]:",
        final_text,
        flags=re.MULTILINE
    )

    final_text = re.sub(
        r"^Hiring Manager,$",
        "Dear [Hiring Manager's Name],",
        final_text,
        flags=re.MULTILINE
    )

    final_text = re.sub(
        r"^Hiring Manager:$",
        "Dear [Hiring Manager's Name]:",
        final_text,
        flags=re.MULTILINE
    )

    return final_text

def extract_resume_contact_header(resume):
    """
    Extract likely contact header lines from the original resume.
    Usually includes name, location, phone, email, LinkedIn/portfolio.
    """
    lines = [line.strip() for line in resume.splitlines() if line.strip()]

    if not lines:
        return []

    header_lines = []

    for line in lines[:5]:
        lower = line.lower()

        # Stop once main resume sections begin
        if lower in {
            "education",
            "experience",
            "professional experience",
            "technical skills",
            "skills",
            "projects",
            "summary",
            "professional summary",
        }:
            break

        header_lines.append(line)

    return header_lines


def postprocess_improved_resume(improved_resume, original_resume):
    """
    Rebuild the resume contact header using the original resume information.
    This prevents duplicate placeholders and preserves available contact info.
    """
    contact_header = extract_resume_contact_header(original_resume)

    if not contact_header:
        return improved_resume.strip()

    final_text = improved_resume.strip()

    section_headings = [
        "EDUCATION",
        "SUMMARY",
        "PROFESSIONAL SUMMARY",
        "RELEVANT SKILLS",
        "TECHNICAL SKILLS",
        "SKILLS",
        "EXPERIENCE",
        "PROFESSIONAL EXPERIENCE",
        "WORK EXPERIENCE",
        "PROJECTS",
        "RELATED PROJECTS",
        "LEADERSHIP",
        "CERTIFICATIONS",
    ]

    # Find the first real resume section in the improved resume.
    first_section_index = None

    for heading in section_headings:
        match = re.search(rf"(?im)^\s*{re.escape(heading)}\s*:?\s*$", final_text)
        if match:
            if first_section_index is None or match.start() < first_section_index:
                first_section_index = match.start()

    # If a section heading is found, remove everything before it.
    # This removes any model-generated contact header or placeholder header.
    if first_section_index is not None:
        body_text = final_text[first_section_index:].strip()
    else:
        body_text = final_text

    # Detect what the original resume already has.
    original_header_text = "\n".join(contact_header)

    original_has_phone = bool(
        re.search(r"\d{3}[-.\s]\d{3}[-.\s]\d{4}", original_header_text)
    )

    original_has_email = "@" in original_header_text

    original_has_link = bool(
        "linkedin" in original_header_text.lower()
        or "github" in original_header_text.lower()
        or "portfolio" in original_header_text.lower()
        or "http" in original_header_text.lower()
    )

    # Build clean header from original resume.
    clean_header_lines = contact_header.copy()

    missing_items = []

    if not original_has_phone:
        missing_items.append("[Your Phone Number]")

    if not original_has_email:
        missing_items.append("[Your Email]")

    if not original_has_link:
        missing_items.append("[LinkedIn or Portfolio URL]")

    if missing_items:
        clean_header_lines.append(" | ".join(missing_items))

    clean_header_text = "\n".join(clean_header_lines)

    # Final clean output
    final_text = clean_header_text + "\n\n" + body_text

    # Clean excessive blank lines
    final_text = re.sub(r"\n{3,}", "\n\n", final_text).strip()

    return final_text


def postprocess_cover_letter(cover_letter, resume, jd):
    today = datetime.today().strftime("%B %d, %Y")

    candidate_name = extract_candidate_name(resume)
    hiring_manager = extract_hiring_manager_name(jd)

    final_text = cover_letter

    # Replace date before returning to UI
    final_text = final_text.replace("[Date]", today)

    # Replace applicant-side placeholders if candidate name exists
    if candidate_name:
        final_text = final_text.replace("[Your Name]", candidate_name)
        final_text = final_text.replace("[Applicant Name]", candidate_name)

    # Normalize hiring manager placeholder if missing
    if not hiring_manager:
        final_text = re.sub(
            r"^Hiring Manager$",
            "[Hiring Manager's Name]",
            final_text,
            flags=re.MULTILINE
        )

        final_text = final_text.replace(
            "Dear Hiring Manager,",
            "Dear [Hiring Manager's Name],"
        )

        final_text = final_text.replace(
            "Dear Hiring Manager:",
            "Dear [Hiring Manager's Name]:"
        )

    # Ensure employer block is complete but avoid duplicate address placeholders
    final_text = ensure_employer_block(final_text, resume, jd)

    # Ensure greeting starts with Dear
    final_text = normalize_greeting(final_text)

    return final_text


# -----------------------------
# Resume Improvement
# -----------------------------

def improve_resume(resume, jd):
    prompt = f"""
You are an ethical resume optimization assistant.

Your task is to rewrite the user's resume to better align with the job description.

IMPORTANT RULES:
- Do NOT invent skills, tools, certifications, degrees, companies, projects, job titles, or years of experience.
- Do NOT claim the user has experience with a skill unless it is clearly supported by the original resume.
- If the job description asks for a skill that is missing from the resume, do NOT add it as an existing skill.
- You may improve wording, structure, clarity, and emphasize transferable experience.
- You may keep placeholders such as [Your Name] if the original resume does not provide personal information.
- Do not include explanations, notes, or comments after the resume.
- Do not say "This revised resume..." or similar meta-commentary.
- Return only the resume content.

Applicant information completeness rules:
- The improved resume must include a contact header at the top.
- The contact header should include:
  1. Candidate name
  2. Location
  3. Phone number
  4. Email
  5. LinkedIn or portfolio link if available
- If any item is available in the original resume, use it exactly.
- If any required item is missing, use these exact placeholders:
  [Your Name]
  [Your Location]
  [Your Phone Number]
  [Your Email]
  [LinkedIn or Portfolio URL]
- Do NOT omit missing contact fields.
- Preserve the original candidate name, location, email, phone number, LinkedIn, or portfolio information if they appear in the original resume.
- Do NOT replace existing applicant information with placeholders.
- Use placeholders only for applicant information that is truly missing from the original resume.

Few-shot example:

Original resume bullet:
"Worked on APIs and databases."

Safe improved bullet:
"Developed and maintained backend APIs and supported SQL database operations for web applications."

Unsafe improved bullet:
"Built advanced Python machine learning systems with five years of experience."

Why unsafe:
The original bullet does not support Python, machine learning, or five years of experience.

Original Resume:
{resume}

Job Description:
{jd}

Rewrite the resume safely and ethically.
Focus on:
- stronger wording
- better organization
- emphasizing existing relevant experience
- transferable skills that are actually supported by the resume

Return only the improved resume.
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.25
    )

    improved_resume = response.choices[0].message.content

    return postprocess_improved_resume(improved_resume, resume)

# -----------------------------
# Improvement Explanation
# -----------------------------

def explain_improvement(original, improved, jd):
    prompt = f"""
You are analyzing how an AI-improved resume became better aligned with a job description.

Job Description:
{jd}

Original Resume:
{original}

Improved Resume:
{improved}

Explain the most important improvements made.
Base your explanation only on the differences between the Original Resume and Improved Resume provided above.
Do not mention improvements that are not visible in the Improved Resume.

IMPORTANT:
- Do not say the resume added fake skills.
- Focus on wording, structure, clarity, transferable experience, and alignment.
- Return exactly 3 to 5 short bullet points.
- Do not include an introduction or conclusion.
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )

    return response.choices[0].message.content


# -----------------------------
# Missing Skills
# -----------------------------

def suggest_missing_skills(resume, jd):
    prompt = f"""
You are a career development assistant.

Compare the user's original resume/profile with the job description.

Your task:
1. Identify important qualifications, skills, tools, domain knowledge, certifications, or experiences required by the job description.
2. Check which of them are not clearly supported by the user's original resume.
3. Suggest what the user should learn, practice, or gain real experience in.

IMPORTANT RULES:
- Do NOT assume this is a software engineering job.
- This should work for any job field, such as business, healthcare, education, finance, design, engineering, hospitality, marketing, or technology.
- Do NOT tell the user to falsely add missing qualifications to the resume.
- Only list missing items that are important for the target job.
- Return 3 to 6 bullet points.
- If there are no major missing qualifications, say that no major gaps were detected.
- Base the missing-skills analysis only on the Original Resume and Job Description.
- If a skill is only weakly implied but not clearly supported, list it as a development area rather than claiming the user already has it.

Original Resume:
{resume}

Job Description:
{jd}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )

    return response.choices[0].message.content


# -----------------------------
# Cover Letter
# -----------------------------

def generate_cover_letter(resume, jd):
    today = datetime.today().strftime("%B %d, %Y")

    prompt = f"""
You are an ethical cover letter writing assistant.

Write a tailored cover letter based on the user's resume and the job description.

IMPORTANT RULES:
- Do NOT invent skills, tools, certifications, degrees, companies, projects, job titles, or years of experience.
- Do NOT claim the user has experience with something unless it is clearly supported by the resume.
- If the job description requires something missing from the resume, do not pretend the user has it.
- Emphasize transferable and existing experience.
- Keep the tone professional, concise, and suitable for a job application.

Applicant information rules:
- You MUST include ALL of the following at the top:
  1. Name
  2. Location
  3. Phone number
  4. Email
- If information exists → use it EXACTLY
- If missing → use placeholders EXACTLY as below:
  [Your Name]
  [Your Location]
  [Your Phone Number]
  [Your Email]
- DO NOT omit any of these.

Employer information rules:
- The cover letter must include a complete employer information block after the date.
- The employer information block must include:
  1. Hiring manager name
  2. Company name
  3. Company address
  4. City, State, ZIP
- If the job description includes any of this employer information, use it exactly.
- If the job description does not include any employer information, use these exact placeholders:
  [Hiring Manager's Name]
  [Company Name]
  [Company Address]
  [City, State, ZIP]
- Do NOT omit the employer information block.
- Do NOT write only "Hiring Manager" as a name.

Date rule:
- Use this date directly: {today}
- Do NOT output [Date].

Format:
- Start with the applicant's available contact information from the resume.
- Then include the date: {today}
- Then include the employer information block.
- Then write the greeting in this exact form:
  Dear [Hiring Manager's Name],
  or Dear [Actual Hiring Manager Name],
- Do NOT output a standalone [Hiring Manager's Name] line as the greeting.
- Then write 3 to 4 concise body paragraphs.
- End with "Sincerely," followed by the applicant's name from the resume if available.
- Return only the cover letter.

Resume:
{resume}

Job Description:
{jd}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )

    cover_letter = response.choices[0].message.content

    return postprocess_cover_letter(cover_letter, resume, jd)