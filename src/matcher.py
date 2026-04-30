import re
from collections import Counter

STOPWORDS = {
    "the", "a", "an", "and", "or", "to", "of", "in", "for", "with", "on", "at",
    "by", "from", "as", "is", "are", "be", "this", "that", "we", "you", "your",
    "our", "will", "can", "have", "has", "had", "it", "they", "their", "not",
    "but", "if", "then", "than", "into", "about", "more", "most", "such",
    "looking", "candidate", "should", "required", "plus", "position", "intern",
    "role", "team", "join", "seeking", "motivated", "responsibilities",
    "requirements", "qualifications", "preferred", "description", "company",
    "work", "working", "assist", "participate", "including", "include",
    "focus", "focused", "provides", "hands", "real", "world", "modern",
    "practices", "experience", "skills", "knowledge", "familiarity",
    "understanding", "exposure", "basic", "strong", "good", "excellent",
    "about", "role", "provide", "providing", "based", "using", "used",
    "various", "high", "level", "new", "current", "future"
}

SECTION_MARKERS = [
    "requirements",
    "required qualifications",
    "preferred qualifications",
    "preferred",
    "responsibilities",
    "what you will do",
    "what you'll do",
    "skills",
    "qualifications",
    "technologies",
    "tools",
    "must have",
    "nice to have",
]


def extract_relevant_jd_text(jd):
    """
    Generic extraction of the most requirement-heavy parts of a JD.
    If section markers are found, use text from those sections.
    If not, fall back to the full JD.
    """
    if not jd:
        return ""

    lines = jd.splitlines()
    selected_lines = []
    capture = False

    for line in lines:
        clean = line.strip()
        lower = clean.lower().rstrip(":")

        if any(marker in lower for marker in SECTION_MARKERS):
            capture = True
            selected_lines.append(clean)
            continue

        if capture:
            selected_lines.append(clean)

    selected_text = "\n".join(selected_lines).strip()
    return selected_text if selected_text else jd


def extract_keywords(text):
    words = re.findall(r"\b[\w+#.]+\b", text.lower())
    return [
        word for word in words
        if word not in STOPWORDS and len(word) > 2
    ]


def compute_match_score(resume, jd):
    """
    Generic internal resume-JD alignment score.

    This scorer is intentionally not job-specific.
    It focuses on important JD sections and measures explicit wording overlap.
    """

    relevant_jd = extract_relevant_jd_text(jd)

    resume_words = extract_keywords(resume)
    jd_words = extract_keywords(relevant_jd)

    if not jd_words:
        return 0

    resume_counter = Counter(resume_words)
    jd_counter = Counter(jd_words)

    jd_unique = set(jd_words)
    matched = [word for word in jd_unique if word in resume_counter]

    # 1. Keyword coverage
    coverage_score = len(matched) / len(jd_unique)

    # 2. Weighted score based on repeated JD terms
    total_weight = 0
    matched_weight = 0

    for word, freq in jd_counter.items():
        weight = 1 + min(freq - 1, 2) * 0.5
        total_weight += weight
        if word in resume_counter:
            matched_weight += weight

    weighted_score = matched_weight / total_weight if total_weight else 0

    # 3. Resume density: rewards clear explicit alignment but caps repetition
    matched_frequency = sum(min(resume_counter[word], 3) for word in matched)
    density_score = min(matched_frequency / max(len(jd_unique), 1), 1)

    raw_score = (
        0.50 * coverage_score +
        0.35 * weighted_score +
        0.15 * density_score
    ) * 100

    # 4. Calibration for human-readable demo score
    # This keeps weak matches low but avoids under-scoring clearly related resumes.
    scaled_score = raw_score * 1.5

    return round(min(scaled_score, 100), 2)
