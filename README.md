# AI Resume Matcher & Optimizer

## Project Overview

AI Resume Matcher & Optimizer is an AI-driven personal branding assistant that helps users improve their resumes and generate tailored cover letters based on a target job description. The system analyzes the user's resume/profile, compares it with the job description, calculates an internal match score, rewrites the resume safely, identifies missing skills, and supports document export.

This project follows the Intelligent Resume & Portfolio Builder scenario. It focuses on personalization, job-market alignment, ethical AI generation, and user-centered UX.

## Problem Statement

Job seekers often struggle to tailor their resumes and cover letters for each job application. Many applicants either submit generic resumes or over-adjust their resumes in ways that may exaggerate or misrepresent their experience.

This project solves that problem by creating an AI assistant that improves resume-job alignment while avoiding fabricated skills or unsupported experience.

## Target Users

- Students applying for internships
- Entry-level job seekers
- Career changers
- Professionals customizing resumes for specific job descriptions
- University career service users

## Value Proposition

The system helps users:

- Understand how well their resume matches a job description
- Improve resume wording and structure
- Generate a job-specific cover letter
- Identify missing skills honestly
- Avoid adding unsupported or fake qualifications
- Export improved documents as TXT or PDF

## Key Features

### 1. Resume and Job Description Input

Users can either paste plain text or upload files.

Supported input formats:

- TXT
- PDF
- DOCX

### 2. Input Validation

The system validates resume/profile input and job description input independently.

It rejects unrelated or meaningless inputs while still allowing cross-field comparisons, such as a customer service resume being compared with a software engineering job.

### 3. Resume Match Scoring

The application calculates an internal keyword-based alignment score between the resume and the job description.

It displays:

- Original match score
- Improved match score
- Score increase

This score is not an official ATS score. It is used as a measurable project indicator.

### 4. Ethical Resume Improvement

The AI rewrites the resume to better align with the job description while following strict safety rules:

- Do not invent skills
- Do not invent experience
- Do not add unsupported tools or certifications
- Emphasize existing and transferable experience
- Preserve or request missing contact information through placeholders

### 5. Missing Skills / Development Suggestions

The system identifies important qualifications from the job description that are not clearly supported by the original resume.

Instead of adding those missing skills to the resume, the system recommends what the user should learn, practice, or gain real experience in.

### 6. Cover Letter Generation

The system generates a tailored cover letter based on:

- User resume
- Job description
- Company information if provided
- Hiring manager information if provided
- Company address if provided

If important applicant or employer information is missing, placeholders are generated for user correction.

### 7. Human-in-the-Loop Placeholder Correction

If the generated resume or cover letter contains placeholders such as:

- [Your Phone Number]
- [Your Email]
- [Hiring Manager's Name]
- [Company Name]

the app prompts the user to fill in the missing information before downloading the final output.

The same placeholder only needs to be entered once and is applied to both the resume and cover letter.

### 8. Export Outputs

Users can download:

- Improved resume as TXT
- Cover letter as TXT
- Improved resume as PDF
- Cover letter as PDF

The PDF export includes basic formatting for resumes and cover letters.

## Technical Architecture

The system follows a modular architecture:

```text
User Input
   ↓
File Reader / Text Input
   ↓
Input Validation
   ↓
Resume-JD Match Scoring
   ↓
LLM Resume Rewriter
   ↓
LLM Improvement Explanation
   ↓
LLM Missing Skills Advisor
   ↓
LLM Cover Letter Generator
   ↓
Placeholder Detection and Human Correction
   ↓
TXT / PDF Export