import os
from datetime import datetime
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize Gemini API if key is present
API_KEY = os.getenv("GEMINI_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)


def calculate_priority_score(exam_date_str, difficulty, confidence):
    """
    Computes an Urgency-Difficulty-Confidence (UDC) priority score.
    Higher score indicates:
      - Closer exam deadline (urgency)
      - Higher subject difficulty
      - Lower student confidence
    """
    try:
        exam_date = datetime.strptime(exam_date_str, "%Y-%m-%d").date()
        today = datetime.now().date()
        days_left = max((exam_date - today).days, 1)
    except (ValueError, TypeError):
        days_left = 7

    # Heuristic: (Difficulty + 1) / (Confidence + 0.5) * (1 / sqrt(Days Left))
    urgency_factor = 1.0 / (days_left ** 0.5)
    gap_factor = (difficulty + 1) / (confidence + 0.5)
    priority_score = round(gap_factor * urgency_factor * 10, 2)
    
    return priority_score, days_left


def generate_heuristic_schedule(topics, daily_hours_available):
    """
    Distributes daily study hours dynamically among pending topics
    proportional to their priority scores.
    
    Expected tuple format per topic:
    (id, subject, topic, exam_date, difficulty, confidence, est_hours, completed)
    """
    # Filter only pending/incomplete topics (completed == 0)
    uncompleted = [t for t in topics if t[7] == 0]
    if not uncompleted:
        return []

    scored_topics = []
    for item in uncompleted:
        tid, subj, name, edate, diff, conf, est_hrs, _ = item
        score, days_left = calculate_priority_score(edate, diff, conf)
        scored_topics.append({
            "id": tid,
            "subject": subj,
            "topic": name,
            "exam_date": edate,
            "days_left": days_left,
            "priority": score,
            "est_hours": est_hrs
        })

    # Sort descending by priority weight
    scored_topics.sort(key=lambda x: x["priority"], reverse=True)
    total_priority = sum(x["priority"] for x in scored_topics)

    schedule = []
    for item in scored_topics:
        if total_priority > 0:
            assigned = round((item["priority"] / total_priority) * daily_hours_available, 2)
        else:
            assigned = round(daily_hours_available / len(scored_topics), 2)

        # Cap daily allocated hours by the estimated remaining hours required
        assigned = min(assigned, float(item["est_hours"]))
        
        schedule.append({
            "id": item["id"],
            "subject": item["subject"],
            "topic": item["topic"],
            "days_left": item["days_left"],
            "priority_score": item["priority"],
            "recommended_hours": assigned
        })

    return schedule


def generate_ai_advice(topic_name, subject, difficulty, confidence):
    """
    Uses Google Gemini (gemini-1.5-flash) to produce tailored revision tips.
    Falls back gracefully if the API key is not supplied or fails.
    """
    if not API_KEY:
        return (
            f"1. Break '{topic_name}' into targeted 25-minute Pomodoro study blocks.\n"
            f"2. Write out summary sheets and active recall flashcards.\n"
            f"3. Solve 3–5 previous year questions or practice problems on {subject}."
        )

    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = (
            f"Provide a 3-bullet-point study strategy for the topic '{topic_name}' "
            f"in the subject '{subject}'. Difficulty rating: {difficulty}/5, "
            f"current confidence rating: {confidence}/5. Keep each bullet point action-oriented and brief."
        )
        response = model.generate_content(prompt)
        return response.text
    except Exception:
        return (
            f"Focus on active recall for '{topic_name}', test core definitions, "
            f"and practice past questions under timed conditions."
        )
