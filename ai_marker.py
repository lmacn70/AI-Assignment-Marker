import json
from openai import OpenAI

client = OpenAI()


def mark_student_submission(task_text, criteria_text, student_text, student_name):
    prompt = f"""
You are an experienced Queensland mathematics teacher.

Mark the student's assignment using the task sheet and criteria sheet.

Return JSON only. No markdown. No explanation outside JSON.

Use this structure:

{{
  "student_name": "{student_name}",
  "criteria_results": [
    {{
      "criterion": "Criterion name",
      "grade": "A/B/C/D/E or Not Yet Demonstrated",
      "feedback": "Specific feedback explaining what was demonstrated and what needs improvement."
    }}
  ],
  "overall_grade": "A/B/C/D/E",
  "overall_feedback": "Clear overall feedback for the student."
}}

TASK SHEET:
{task_text}

CRITERIA SHEET:
{criteria_text}

STUDENT SUBMISSION:
{student_text}
"""

    response = client.responses.create(
        model="gpt-5.5",
        input=prompt,
    )

    result_text = response.output_text.strip()

    try:
        return json.loads(result_text)
    except json.JSONDecodeError:
        return {
            "student_name": student_name,
            "criteria_results": [],
            "overall_grade": "ERROR",
            "overall_feedback": result_text,
        }