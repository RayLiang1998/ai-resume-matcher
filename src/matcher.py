import re
from collections import Counter

STOPWORDS = {
    "the", "a", "an", "and", "or", "to", "of", "in", "for", "with", "on", "at",
    "by", "from", "as", "is", "are", "be", "this", "that", "we", "you", "your",
    "our", "will", "can", "have", "has", "had", "it", "they", "their", "not",
    "but", "if", "then", "than", "into", "about", "more", "most", "such",
    "looking", "candidate", "should", "required", "plus", "position", "intern"
}


def extract_keywords(text):
    words = re.findall(r"\b[\w+#]+\b", text.lower())
    return [
        word for word in words
        if word not in STOPWORDS and len(word) > 2
    ]


def compute_match_score(resume, jd):
    resume_words = extract_keywords(resume)
    jd_words = extract_keywords(jd)

    if not jd_words:
        return 0

    resume_counter = Counter(resume_words)
    jd_unique_words = set(jd_words)

    # 1. Basic keyword coverage: how many JD keywords appear in the resume
    matched_keywords = [word for word in jd_unique_words if word in resume_counter]
    coverage_score = len(matched_keywords) / len(jd_unique_words)

    # 2. Relevance density: how often JD keywords appear in the resume
    matched_frequency = sum(resume_counter[word] for word in matched_keywords)
    density_score = min(matched_frequency / max(len(jd_unique_words), 1), 1)

    # 3. Weighted score
    raw_score = (0.65 * coverage_score + 0.35 * density_score) * 100

    # 4. Scale score to make it easier to interpret in demo
    # This keeps weak matches low but allows good improved resumes to reach 80+.
    scaled_score = min(raw_score * 1.25, 100)

    return round(scaled_score, 2)