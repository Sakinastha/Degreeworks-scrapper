import re
import json

def parse_degreeworks_txt(txt_path, json_path="parsed_output.json"):
    with open(txt_path, "r", encoding="utf-8") as f:
        text = f.read()

    # Initialize JSON structure
    data = {
        "student_name": None,
        "gpa": None,
        "sections": []
    }



    # --- Extract GPA ---
    gpa_match = re.search(r"Overall GPA\s*([\d\.]+)", text)
    if gpa_match:
        data["gpa"] = float(gpa_match.group(1))

    # --- Section headers to look for ---
    section_headers = [
        "General Education Program Requirements",
        "Major Requirements",
        "Complementary Studies Program",
        "Computer Science Requirements",
        "Electives",
        "Senior Project"
    ]

    # --- Split text into sections based on headers ---
    sections = []
    for i, header in enumerate(section_headers):
        start = text.find(header)
        if start == -1:
            continue
        end = (
            text.find(section_headers[i + 1], start)
            if i + 1 < len(section_headers)
            else len(text)
        )
        section_text = text[start:end]

        section_data = {"name": header, "completed_courses": [], "remaining_requirements": []}

        # --- Extract completed courses ---
        course_pattern = re.compile(
            r"Course\s*(?P<code>\w+\s*\d+).*?"
            r"Title\s*(?P<title>.*?)\s*"
            r"Grade\s*(?P<grade>[A-Z]+).*?"
            r"Credits\s*(?P<credits>[\d\(\)]+).*?"
            r"Term\s*(?P<term>[\w\s\d\-]+)",
            re.DOTALL
        )

        for match in course_pattern.finditer(section_text):
            section_data["completed_courses"].append({
                "course": match.group("code").strip(),
                "title": match.group("title").strip(),
                "grade": match.group("grade").strip(),
                "credits": match.group("credits").strip(),
                "term": match.group("term").strip()
            })

        # --- Extract remaining requirements ---
        unmet_pattern = re.compile(r"Still needed[:\s]*(.*?)(?:Course|$)", re.DOTALL)
        for match in unmet_pattern.finditer(section_text):
            req_text = match.group(1).strip().replace("\n", " ")
            if req_text:
                section_data["remaining_requirements"].append(req_text)

        sections.append(section_data)

    data["sections"] = sections

    # --- Write structured JSON file ---
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print(f"✅ JSON file created: {json_path}")
    return data
