import re
from typing import Dict, List, Optional


QUESTION_BANK: List[Dict] = [
    {
        "category": "background",
        "canonical_question": "Tell me about yourself.",
        "strategy": "Use a short present-past-future structure: who you are now, relevant background, and why you are here.",
        "examples": [
            "tell me about yourself",
            "who are you",
            "introduce yourself",
            "can you introduce yourself",
            "walk me through your background",
            "tell us a little about yourself",
        ],
    },
    {
        "category": "education",
        "canonical_question": "What have you studied so far?",
        "strategy": "Summarize your education briefly, then highlight the subjects most relevant to the role or programme.",
        "examples": [
            "what have you studied so far",
            "what did you study",
            "tell me about your studies",
            "what is your academic background",
            "can you describe your education",
        ],
    },
    {
        "category": "experience",
        "canonical_question": "What has been your experience so far?",
        "strategy": "Give a concise overview of relevant experience, then mention one concrete project, skill, or result.",
        "examples": [
            "what has been your experience",
            "tell me about your experience",
            "what experience do you have",
            "walk me through your experience",
            "describe your relevant experience",
            "what have you worked on",
        ],
    },
    {
        "category": "motivation",
        "canonical_question": "Why are you interested in this role?",
        "strategy": "Connect your interests, skills, and goals to the specific role. Mention what you hope to contribute and learn.",
        "examples": [
            "why are you interested in this role",
            "why do you want this job",
            "why this position",
            "what interests you about this role",
            "why are you applying",
        ],
    },
    {
        "category": "university_fit",
        "canonical_question": "Why did you choose this university?",
        "strategy": "Connect your academic goals to specific strengths of the university, programme, environment, or opportunities.",
        "examples": [
            "why did you choose this university",
            "why this university",
            "why do you want to study here",
            "why have you chosen our university",
            "what attracts you to this university",
        ],
    },
    {
        "category": "course_fit",
        "canonical_question": "Why did you choose this course or programme?",
        "strategy": "Explain your interest in the subject, connect it to your background, and show how it supports your future goals.",
        "examples": [
            "why did you choose this course",
            "why this programme",
            "why this program",
            "why did you choose this major",
            "why did you choose that particular major",
            "what made you choose this field",
            "why are you interested in this subject",
        ],
    },
    {
        "category": "grades",
        "canonical_question": "What grades did you get?",
        "strategy": "Answer honestly and briefly, then contextualize with progress, relevant strengths, projects, or achievements.",
        "examples": [
            "what grades did you get",
            "what are your grades",
            "what was your gpa",
            "how did you perform academically",
            "tell me about your academic results",
        ],
    },
    {
        "category": "strengths",
        "canonical_question": "What are your strengths?",
        "strategy": "Name 2-3 strengths, support each with evidence, and connect them to the role or programme.",
        "examples": [
            "what are your strengths",
            "tell me about your strengths",
            "what do you do best",
            "what are you good at",
            "what would you say are your strongest skills",
        ],
    },
    {
        "category": "weaknesses",
        "canonical_question": "What are your weaknesses?",
        "strategy": "Choose a real but manageable weakness, explain how you are improving it, and avoid sounding careless.",
        "examples": [
            "what are your weaknesses",
            "tell me about a weakness",
            "what do you need to improve",
            "what is an area for improvement",
            "what would you like to get better at",
        ],
    },
    {
        "category": "project",
        "canonical_question": "Tell me about a project you worked on.",
        "strategy": "Use situation-task-action-result. Explain the goal, your role, technical choices, and outcome.",
        "examples": [
            "tell me about a project",
            "describe a project you worked on",
            "what project are you proud of",
            "walk me through one of your projects",
            "tell me about your best project",
        ],
    },
    {
        "category": "challenge",
        "canonical_question": "Describe a challenge you faced.",
        "strategy": "Use situation-task-action-result. Focus on what you did, what you learned, and how you adapted.",
        "examples": [
            "describe a challenge you faced",
            "tell me about a challenge",
            "tell me about a difficult situation",
            "what was a challenge you overcame",
            "describe a time you struggled",
        ],
    },
    {
        "category": "failure",
        "canonical_question": "Tell me about a time you failed.",
        "strategy": "Choose a real example, take responsibility, explain the lesson, and show changed behavior.",
        "examples": [
            "tell me about a time you failed",
            "describe a failure",
            "what is a mistake you made",
            "tell me about a mistake",
            "what did you learn from failure",
        ],
    },
    {
        "category": "teamwork",
        "canonical_question": "Tell me about a time you worked in a team.",
        "strategy": "Describe the team goal, your contribution, communication, and the result.",
        "examples": [
            "tell me about teamwork",
            "describe a time you worked in a team",
            "give an example of teamwork",
            "how do you work in teams",
            "tell me about a group project",
        ],
    },
    {
        "category": "leadership",
        "canonical_question": "Tell me about a time you showed leadership.",
        "strategy": "Show how you took responsibility, helped others, made a decision, or improved the outcome.",
        "examples": [
            "tell me about a time you showed leadership",
            "describe your leadership experience",
            "have you led a team",
            "give an example of leadership",
            "how do you lead others",
        ],
    },
    {
        "category": "conflict",
        "canonical_question": "Tell me about a conflict and how you handled it.",
        "strategy": "Show calm communication, listening, problem solving, and a constructive result.",
        "examples": [
            "tell me about a conflict",
            "describe a disagreement",
            "how do you handle conflict",
            "tell me about a difficult teammate",
            "how did you resolve a disagreement",
        ],
    },
    {
        "category": "problem_solving",
        "canonical_question": "How do you solve problems?",
        "strategy": "Explain your process: understand the problem, break it down, test options, learn from feedback.",
        "examples": [
            "how do you solve problems",
            "describe your problem solving process",
            "tell me about a problem you solved",
            "how do you approach difficult problems",
            "give an example of problem solving",
        ],
    },
    {
        "category": "pressure",
        "canonical_question": "How do you work under pressure?",
        "strategy": "Explain how you prioritize, stay calm, communicate, and deliver. Use a concrete example.",
        "examples": [
            "how do you work under pressure",
            "can you handle pressure",
            "tell me about a stressful situation",
            "how do you manage stress",
            "how do you handle deadlines",
        ],
    },
    {
        "category": "goals",
        "canonical_question": "Where do you see yourself in the future?",
        "strategy": "Give realistic goals connected to learning, contribution, and growth in the field.",
        "examples": [
            "where do you see yourself in five years",
            "what are your future goals",
            "what do you want to do after this",
            "what are your career goals",
            "where do you see your career going",
        ],
    },
    {
        "category": "fit",
        "canonical_question": "Why should we choose you?",
        "strategy": "Summarize fit: relevant skills, evidence, motivation, and what makes you a strong match.",
        "examples": [
            "why should we choose you",
            "why should we hire you",
            "what makes you a good fit",
            "why are you the right candidate",
            "what can you bring to us",
        ],
    },
    {
        "category": "closing",
        "canonical_question": "Do you have any questions for us?",
        "strategy": "Ask thoughtful questions about expectations, team/programme culture, success criteria, or next steps.",
        "examples": [
            "do you have any questions for us",
            "do you have questions for me",
            "what would you like to ask us",
            "is there anything you want to ask",
            "any questions from your side",
        ],
    },
]


def _tokens(text: str) -> List[str]:
    text = re.sub(r"[^a-z0-9 ]+", " ", text.lower())
    stopwords = {
        "the", "a", "an", "to", "of", "and", "or", "in", "on", "for",
        "with", "me", "you", "your", "us", "our", "this", "that",
        "did", "do", "does", "are", "is", "was", "were", "can", "could",
        "would", "should", "about", "tell",
    }
    return [tok for tok in text.split() if tok and tok not in stopwords]


def _jaccard(a: List[str], b: List[str]) -> float:
    set_a = set(a)
    set_b = set(b)

    if not set_a or not set_b:
        return 0.0

    return len(set_a & set_b) / len(set_a | set_b)


def match_interview_question(question_text: str) -> Optional[Dict]:
    query_tokens = _tokens(question_text)

    if not query_tokens:
        return None

    best = None
    best_score = 0.0

    for item in QUESTION_BANK:
        candidates = [item["canonical_question"]] + item.get("examples", [])

        for candidate in candidates:
            score = _jaccard(query_tokens, _tokens(candidate))

            if score > best_score:
                best_score = score
                best = item

    if not best or best_score < 0.18:
        return None

    return {
        "category": best["category"],
        "canonical_question": best["canonical_question"],
        "strategy": best["strategy"],
        "similarity": round(best_score, 3),
    }
