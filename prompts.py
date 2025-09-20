SUMMARY_PROMPT = """
You are an expert explainer. Write a comprehensive, neutral overview of "{topic}".
STRICT FORMAT:
- Output EXACTLY 3 paragraphs, each wrapped in <p> ... </p>. No headings, lists, or extra text.
- Each paragraph must contain 6–8 complete sentences (total 18–24 sentences).
CONTENT SCOPE:
1) Para 1 — definition/scope, why it exists, and the core building blocks.
2) Para 2 — architecture/high availability, security/governance, operations/monitoring/backup.
3) Para 3 — common use cases, benefits vs. trade-offs, pricing basics, compliance, and best practices.
STYLE:
- 9th–12th grade reading level; clear, concise, non-marketing; no code.
- Use concrete examples and avoid repetition.
Only output the three <p> blocks.
"""

# Topic-based (fallback)
FLASHCARDS_PROMPT = """
Generate EXACTLY {n} concise flashcards about "{topic}".
STRICT FORMAT (one pair per block, in this exact order):
Q: <question>
A: <answer>
Rules: No numbering, no bullets, no extra lines between cards, no explanations.
Keep answers 1–2 sentences.
"""

QUIZ_PROMPT = """
Create EXACTLY {n} multiple-choice questions about "{topic}".
STRICT FORMAT for each item:
Q: <question>
Options: A) <opt1> B) <opt2> C) <opt3> D) <opt4>
Answer: <exact correct option text, not the letter>
Rules: No numbering, no extra text, exactly 4 options per question.
Make options plausible and distinct; keep each question concise.
"""

# Summary-anchored (preferred)
FLASHCARDS_FROM_SUMMARY_PROMPT = """
You will receive a study SUMMARY. Create EXACTLY {n} flashcards that are 100% supported by the SUMMARY and add no outside facts.

SUMMARY:
<<<
{summary}
>>>

RULES:
- Use only information present in the SUMMARY. Do not invent new facts.
- Cover different areas of the SUMMARY (definition/building blocks; architecture/HA/security/ops; use cases/costs/best practices).
- STRICT FORMAT for each card (no numbering, no extra lines):
Q: <question>
A: <answer>
- Keep answers concise (1–2 sentences), precise, and faithful to the SUMMARY wording.
"""

QUIZ_FROM_SUMMARY_PROMPT = """
You will receive a study SUMMARY. Write EXACTLY {n} MCQs that are fully supported by the SUMMARY and add no outside facts.

SUMMARY:
<<<
{summary}
>>>

RULES:
- Use only information present in the SUMMARY. If unsure, do not ask about it.
- For each question, provide exactly 4 plausible options; 1 correct, 3 distractors that do not contradict the SUMMARY.
- Prefer using the SUMMARY’s wording for the correct option to reduce ambiguity.
- STRICT FORMAT for each item:
Q: <question>
Options: A) <opt1> B) <opt2> C) <opt3> D) <opt4>
Answer: <exact correct option text, not the letter>
- No explanations, no numbering, no extra text.
"""
