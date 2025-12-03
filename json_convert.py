import re
import json

def parse_degreeworks_txt(txt_path, json_path="parsed_output.json"):
    with open(txt_path, "r", encoding="utf-8") as f:
        text = f.read()

    # Initialize JSON structure with metadata
    data = {
        "student_name": None,
        "gpa": None,
        "advisor": None,
        "transfer_hours": None,
        "classification": None,
        "graduation_status": None,
        "graduation_term": None,
        "major": None,
        "program": None,
        "college": None,
        "academic_standing": None,
        "sections": []
    }

    # --- Extract GPA ---
    gpa_match = re.search(r"Overall GPA\s*([\d\.]+)", text)
    if gpa_match:
        data["gpa"] = float(gpa_match.group(1))

    # --- Extract Advisor ---
    advisor_match = re.search(r"Advisor[:\s]+([\w\s]+?)(?:\n|Format|Degree)", text, re.IGNORECASE)
    if advisor_match:
        data["advisor"] = advisor_match.group(1).strip()

    # --- Extract Transfer Hours ---
    transfer_match = re.search(r"Transfer Hours[:\s]+(\d+)", text, re.IGNORECASE)
    if transfer_match:
        data["transfer_hours"] = int(transfer_match.group(1))

    # --- Extract Classification ---
    classification_match = re.search(r"Classification[:\s]+([\w\-]+)", text, re.IGNORECASE)
    if classification_match:
        data["classification"] = classification_match.group(1).strip()

    # --- Extract Major ---
    major_match = re.search(r"Major[:\s]+([\w\s]+?)(?:\n|Program)", text, re.IGNORECASE)
    if major_match:
        data["major"] = major_match.group(1).strip()

    # --- Extract Program ---
    program_match = re.search(r"Program[:\s]+([\w\s]+?)(?:\n|College)", text, re.IGNORECASE)
    if program_match:
        data["program"] = program_match.group(1).strip()

    # --- Extract College ---
    college_match = re.search(r"College[:\s]+([\w\s,/]+?)(?:\n|Academic)", text, re.IGNORECASE)
    if college_match:
        data["college"] = college_match.group(1).strip()

    # --- Extract Academic Standing ---
    standing_match = re.search(r"Academic Standing[:\s]+([\w\s]+?)(?:\n|Graduation)", text, re.IGNORECASE)
    if standing_match:
        data["academic_standing"] = standing_match.group(1).strip()

    # --- Extract Graduation Application Status ---
    grad_app_match = re.search(r"Graduation Application[:\s]+([\w\s]+?)(?:\n|Graduation Term)", text, re.IGNORECASE)
    if grad_app_match:
        data["graduation_status"] = grad_app_match.group(1).strip()

    # --- Extract Graduation Term ---
    grad_term_match = re.search(r"Graduation Term[:\s]+([\w\s\-]+)", text, re.IGNORECASE)
    if grad_term_match:
        data["graduation_term"] = grad_term_match.group(1).strip()

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
    print(f"📋 Metadata extracted:")
    print(f"   - Advisor: {data['advisor']}")
    print(f"   - Transfer Hours: {data['transfer_hours']}")
    print(f"   - Classification: {data['classification']}")
    print(f"   - Major: {data['major']}")
    print(f"   - Academic Standing: {data['academic_standing']}")
    print(f"   - Graduation Status: {data['graduation_status']}")
    
    return data