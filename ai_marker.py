import json
from pathlib import Path
from openai import OpenAI

client = OpenAI()


def upload_file(file_path):
    file_path = Path(file_path)

    with open(file_path, "rb") as file:
        uploaded_file = client.files.create(
            file=file,
            purpose="user_data"
        )

    return uploaded_file.id


def mark_student_submission(task_file_path, criteria_text, student_file_path, student_name):
    task_file_id = upload_file(task_file_path)
    student_file_id = upload_file(student_file_path)

    marking_instructions = f"""
You are an experienced Queensland mathematics teacher.

You are marking a student assignment.

Use:
1. The original assignment task sheet file.
2. The criteria/rubric text below.
3. The original student submission file.

Important marking rules:
- Use the criteria sheet as the main basis for awarding grades.
- Consider evidence from text, calculations, tables, diagrams, graphs, images, and layout in the student submission.
- Be fair, specific, and evidence-based.
- Do not invent evidence that is not in the student work.
- If a graph, diagram, table, or calculation is missing or unclear, say so.
- Feedback should be useful to the student and suitable for a teacher to give.

Grading scale:
A = Excellent demonstration of the criterion.
B = Strong demonstration of the criterion.
C = Satisfactory demonstration of the criterion.
D = Partial demonstration of the criterion.
E = Minimal demonstration of the criterion.
N = The criterion was not demonstrated or there is insufficient evidence to assess it.

Use N whenever the student has not provided evidence for a criterion.
Do not award E if no evidence exists. Use N instead.

Return JSON only. No markdown. No explanation outside JSON.

CRITERIA / RUBRIC TEXT:
{criteria_text}

Return this exact JSON structure:

{{
  "student_name": "{student_name}",
  "criteria_results": [
    {{
      "criterion": "Criterion name",
      "grade": "A/B/C/D/E/N",
      "feedback": "Specific feedback for this criterion."
    }}
  ],
  "overall_grade": "A/B/C/D/E/N",
  "overall_feedback": "Overall feedback for the student."
}}
"""

    response = client.responses.create(
        model="gpt-5.5",
        input=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_file",
                        "file_id": task_file_id,
                    },
                    {
                        "type": "input_file",
                        "file_id": student_file_id,
                    },
                    {
                        "type": "input_text",
                        "text": marking_instructions,
                    },
                ],
            }
        ],
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
    
    