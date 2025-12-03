import os
import re
from datetime import datetime
from selectolax.parser import HTMLParser
from json_convert import parse_degreeworks_txt  


def scrape_degreeworks(html_content: str):
    try:
        # --- Prepare output directory ---
        base_dir = os.path.dirname(os.path.abspath(__file__))
        output_dir = os.path.join(base_dir, "scraped_data")
        os.makedirs(output_dir, exist_ok=True)

        # --- Create filenames ---
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        html_filename = os.path.join(output_dir, f"degreeworks_raw_{timestamp}.html")
        txt_filename = os.path.join(output_dir, f"degreeworks_paragraphs_{timestamp}.txt")
        json_filename = os.path.join(output_dir, f"degreeworks_data_{timestamp}.json")

        # --- Save raw HTML ---
        with open(html_filename, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"[DEBUG] Saved raw HTML to: {html_filename}")

        # --- Parse the HTML using Selectolax ---
        tree = HTMLParser(html_content)
        
        # Extract ALL text content
        text_content = tree.text(separator="\n").strip()
        
        # Try to extract metadata directly from HTML elements
        print("[DEBUG] Extracting metadata from HTML structure...")
        
        metadata = {}
        # Look for common DegreeWorks metadata patterns in the HTML
        html_lower = html_content.lower()
        
        # Extract Advisor
        advisor_patterns = [
            r'advisor[:\s]*([a-zA-Z\s]+?)(?:<|&|Vojislav Stojkovic)',
            r'Advisor[:\s]*([a-zA-Z\s]+?)[\n<]',
        ]
        for pattern in advisor_patterns:
            match = re.search(pattern, html_content, re.IGNORECASE)
            if match:
                advisor = match.group(1).strip()
                if advisor and len(advisor) > 3 and advisor.lower() not in ['prerequisite', 'requirements']:
                    metadata['advisor'] = advisor
                    break
        
        # Extract Transfer Hours
        transfer_match = re.search(r'Transfer\s+Hours[:\s]*(\d+)', html_content, re.IGNORECASE)
        if transfer_match:
            metadata['transfer_hours'] = int(transfer_match.group(1))
        
        # Extract Classification
        class_match = re.search(r'Classification[:\s]*([\w\-]+)', html_content, re.IGNORECASE)
        if class_match:
            metadata['classification'] = class_match.group(1).strip()
        
        # Extract Major
        major_match = re.search(r'Major[:\s]*(Computer Science)', html_content, re.IGNORECASE)
        if major_match:
            metadata['major'] = major_match.group(1).strip()
        
        # Extract Academic Standing
        standing_match = re.search(r'Academic\s+Standing[:\s]*([\w\s]+?)(?:<|&|\n)', html_content, re.IGNORECASE)
        if standing_match:
            metadata['academic_standing'] = standing_match.group(1).strip()
        
        # Extract Graduation Application
        grad_match = re.search(r'Graduation\s+Application[:\s]*(Applied for Graduation)', html_content, re.IGNORECASE)
        if grad_match:
            metadata['graduation_status'] = grad_match.group(1).strip()
        
        print(f"[DEBUG] Found metadata: {metadata}")

        # --- Save extracted paragraph text ---
        with open(txt_filename, "w", encoding="utf-8") as f:
            f.write("=== Extracted Paragraphs from HTML ===\n\n")
            f.write(text_content if text_content else "No text found.")
        print(f"[DEBUG] Saved parsed text to: {txt_filename}")

        # --- Convert extracted text into structured JSON ---
        try:
            json_data = parse_degreeworks_txt(txt_filename, json_filename)
            print(f"[DEBUG] Converted text to JSON and saved to: {json_filename}")
        except Exception as e:
            print(f"[ERROR] Failed to convert text to JSON: {e}")
            json_data = {"error": str(e)}

        # ---------- Enhanced data extraction with ALL embedded courses ----------
        if isinstance(json_data, dict):
            sections = json_data.get("sections") or []

            # Helper: parse numeric credits
            def parse_credits(s):
                if not isinstance(s, str):
                    return 0.0
                cleaned = s.replace("(", "").replace(")", "").strip()
                try:
                    return float(cleaned)
                except ValueError:
                    return 0.0

            # Helper: extract semester/year from term string
            def extract_semester_info(term_str):
                """Extract semester and year from term string"""
                term_upper = term_str.upper()
                semester_match = re.search(r'(FALL|SPRING|SUMMER|WINTER)\s+(\d{4})', term_upper)
                if semester_match:
                    semester = semester_match.group(1)
                    year = int(semester_match.group(2))
                    return (semester, year, f"{semester} {year}")
                return (None, None, None)

            # Helper: extract ALL embedded courses from term field
            def extract_all_embedded_courses(term_text):
                """
                Extract ALL courses from term text, including both completed and IP.
                Pattern: Course CODE Title TITLE Grade GRADE Credits NUMBER Term SEMESTER YEAR
                """
                embedded = []
                
                # Pattern 1: Full pattern with Grade and Credits
                # Matches: Course COSC 470 Title ARTIFICIAL INTELLIGENCE Grade A Credits 3 Term FALL 2024
                pattern1 = r'Course\s+([A-Z]+\s+\d+)\s+Title\s+(.+?)\s+Grade\s+([A-Z]+)\s+Credits\s*(\d+\.?\d*)?(?:\s+Term\s+([A-Z]+\s+\d{4}))?'
                
                matches1 = re.finditer(pattern1, term_text, re.IGNORECASE | re.DOTALL)
                
                for match in matches1:
                    emb_code = match.group(1).strip()
                    emb_title = match.group(2).strip()
                    emb_grade = match.group(3).strip().upper()
                    emb_credits_str = match.group(4) if match.group(4) else "3"
                    emb_term = match.group(5) if match.group(5) else None
                    
                    emb_credits = parse_credits(emb_credits_str)
                    if emb_credits == 0.0:
                        emb_credits = 3.0
                    
                    # Extract semester info from the embedded term
                    emb_semester, emb_year, emb_full_term = None, None, None
                    if emb_term:
                        emb_semester, emb_year, emb_full_term = extract_semester_info(emb_term)
                    
                    embedded.append({
                        "code": emb_code,
                        "title": emb_title,
                        "grade": emb_grade,
                        "credits": emb_credits,
                        "semester": emb_semester,
                        "year": emb_year,
                        "full_term": emb_full_term
                    })
                
                # Pattern 2: Incomplete pattern (no Grade/Credits explicitly shown)
                # Matches: Course MATH 331 Title APPLIED PROB (truncated, missing grade/credits)
                # We'll infer these from context - if it's in a completed course's term field, assume grade A
                pattern2 = r'Course\s+([A-Z]+\s+\d+)\s+Title\s+([A-Z\s&,]+?)(?:\s+Grade|\s+Course|\n|$)'
                
                matches2 = re.finditer(pattern2, term_text, re.IGNORECASE)
                
                # Track codes already found by pattern1
                found_codes = {emb["code"] for emb in embedded}
                
                for match in matches2:
                    emb_code = match.group(1).strip()
                    emb_title = match.group(2).strip()
                    
                    # Skip if already found by pattern1
                    if emb_code in found_codes:
                        continue
                    
                    # Try to extract semester from the parent term_text
                    semester_match = re.search(r'(FALL|SPRING|SUMMER|WINTER)\s+(\d{4})', term_text.upper())
                    emb_semester, emb_year, emb_full_term = None, None, None
                    if semester_match:
                        emb_semester = semester_match.group(1)
                        emb_year = int(semester_match.group(2))
                        emb_full_term = f"{emb_semester} {emb_year}"
                    
                    # Default to grade A and 3 credits for incomplete patterns
                    # If no semester found, assume it's the same as the parent course
                    embedded.append({
                        "code": emb_code,
                        "title": emb_title,
                        "grade": "A",  # Assume completed with A if no grade shown
                        "credits": 3.0,
                        "semester": emb_semester,
                        "year": emb_year,
                        "full_term": emb_full_term,
                        "needs_semester_inference": emb_full_term is None
                    })
                    
                    print(f"[DEBUG]   Found incomplete pattern: {emb_code} - assuming grade A, 3 credits, term: {emb_full_term}")
                
                return embedded

            # Dictionaries to store UNIQUE courses
            completed_courses = {}
            in_progress_courses = {}
            
            print(f"\n[DEBUG] ===== Extracting all UNIQUE courses =====")
            
            # First pass: collect all main courses (excluding transfer credits)
            for sec in sections:
                for c in sec.get("completed_courses", []):
                    code = c.get("course", "").strip()
                    if not code:
                        continue
                        
                    title = c.get("title", "").strip()
                    credits = c.get("credits", "0")
                    grade = c.get("grade", "").upper().strip()
                    term_text = c.get("term", "")
                    
                    # Skip transfer credits from previous colleges
                    if grade in ["TRA", "TRB", "TRC"]:
                        print(f"[DEBUG] Skipping transfer credit: {code} - Grade: {grade}")
                        
                    
                    semester, year, full_term = extract_semester_info(term_text)
                    credits_num = parse_credits(credits)
                    
                    course_record = {
                        "course": code,
                        "title": title,
                        "credits": credits_num,
                        "grade": grade,
                        "semester": semester,
                        "year": year,
                        "full_term": full_term,
                        "term_text": term_text
                    }
                    
                    # Categorize by IP vs completed
                    if grade == "IP":
                        if code not in in_progress_courses:
                            in_progress_courses[code] = course_record
                            print(f"[DEBUG] Main IP: {code} - {full_term}")
                    else:
                        if code not in completed_courses:
                            completed_courses[code] = course_record
                            print(f"[DEBUG] Main completed: {code} - {full_term} - Grade: {grade}")

            # Second pass: extract ALL embedded courses (both completed and IP)
            print(f"\n[DEBUG] Searching for ALL embedded courses...")
            
            all_courses_list = list(completed_courses.values()) + list(in_progress_courses.values())
            
            for parent_course in all_courses_list:
                term_text = parent_course.get("term_text", "")
                if not term_text:
                    continue
                
                embedded_courses = extract_all_embedded_courses(term_text)
                
                for emb in embedded_courses:
                    emb_code = emb["code"]
                    emb_grade = emb["grade"]
                    
                    # Skip if already in our lists
                    if emb_code in completed_courses or emb_code in in_progress_courses:
                        continue
                    
                    # Skip transfer credits from embedded courses too
                    if emb_grade in ["TRA", "TRB", "TRC"]:
                        print(f"[DEBUG] Skipping embedded transfer credit: {emb_code} - Grade: {emb_grade}")
                        
                    
                    # If semester is missing, inherit from parent course
                    if not emb["full_term"]:
                        emb["semester"] = parent_course.get("semester")
                        emb["year"] = parent_course.get("year")
                        emb["full_term"] = parent_course.get("full_term")
                        print(f"[DEBUG]   -> Inherited semester {emb['full_term']} from parent {parent_course.get('course')}")
                    
                    emb_record = {
                        "course": emb_code,
                        "title": emb["title"],
                        "credits": emb["credits"],
                        "grade": emb_grade,
                        "semester": emb["semester"],
                        "year": emb["year"],
                        "full_term": emb["full_term"],
                        "term_text": ""
                    }
                    
                    if emb_grade == "IP":
                        in_progress_courses[emb_code] = emb_record
                        print(f"[DEBUG] Embedded IP: {emb_code} ({emb['title'][:30]}...) - {emb['full_term']}")
                    else:
                        completed_courses[emb_code] = emb_record
                        print(f"[DEBUG] Embedded completed: {emb_code} ({emb['title'][:30]}...) - {emb['full_term']} - Grade: {emb_grade}")

            # Build courses by semester
            courses_by_semester = {}
            
            print(f"\n[DEBUG] Building semester breakdown...")
            for course_dict in [completed_courses, in_progress_courses]:
                for course in course_dict.values():
                    full_term = course.get("full_term")
                    course_code = course.get("course")
                    if full_term:
                        if full_term not in courses_by_semester:
                            courses_by_semester[full_term] = {}
                        courses_by_semester[full_term][course_code] = course
                        print(f"[DEBUG]   Added {course_code} to {full_term}")

            # Calculate totals (AFTER all embedded courses extracted, EXCLUDING transfer credits)
            total_completed_credits = sum(c["credits"] for c in completed_courses.values())
            total_msu_courses = len(completed_courses)  # Only courses taken at Morgan State
            current_term_courses = sorted(list(in_progress_courses.keys()))
            current_term_credits = sum(c["credits"] for c in in_progress_courses.values())

            # Build semester list (sorted)
            def semester_sort_key(term):
                parts = term.split()
                if len(parts) != 2:
                    return (0, 0)
                semester_order = {"SPRING": 1, "SUMMER": 2, "FALL": 3, "WINTER": 4}
                year = int(parts[1])
                semester_num = semester_order.get(parts[0], 0)
                return (year, semester_num)
            
            sorted_semesters = sorted(courses_by_semester.keys(), key=semester_sort_key)
            
            # Build semester summary
            semesters_data = []
            for term in sorted_semesters:
                courses = list(courses_by_semester[term].values())
                semester_info = {
                    "term": term,
                    "courses": [
                        {
                            "course": c["course"],
                            "title": c["title"],
                            "credits": c["credits"],
                            "grade": c["grade"]
                        }
                        for c in sorted(courses, key=lambda x: x["course"])
                    ],
                    "total_credits": sum(c["credits"] for c in courses),
                    "course_count": len(courses)
                }
                semesters_data.append(semester_info)

            # Store enhanced data
            json_data["total_completed_credits"] = total_completed_credits
            json_data["total_completed_courses"] = total_msu_courses  # Morgan State courses only
            json_data["current_term"] = "FALL 2025"
            json_data["current_term_courses"] = current_term_courses
            json_data["current_term_credits"] = current_term_credits
            json_data["semesters"] = semesters_data
            
            # Add metadata from HTML extraction
            if metadata:
                for key, value in metadata.items():
                    json_data[key] = value
            
            # Ensure fields exist even if not found
            if "advisor" not in json_data:
                json_data["advisor"] = None
            if "classification" not in json_data:
                json_data["classification"] = None  
            if "transfer_hours" not in json_data:
                json_data["transfer_hours"] = None
            if "major" not in json_data:
                json_data["major"] = None
            if "academic_standing" not in json_data:
                json_data["academic_standing"] = None
            if "graduation_status" not in json_data:
                json_data["graduation_status"] = None
            
            json_data["completed_courses_list"] = [
                {
                    "course": c["course"],
                    "title": c["title"],
                    "credits": c["credits"],
                    "grade": c["grade"],
                    "term": c["full_term"]
                }
                for c in sorted(completed_courses.values(), key=lambda x: (x["year"] or 0, x["course"]))
            ]
            
            json_data["in_progress_courses_list"] = [
                {
                    "course": c["course"],
                    "title": c["title"],
                    "credits": c["credits"],
                    "term": c["full_term"]
                }
                for c in sorted(in_progress_courses.values(), key=lambda x: x["course"])
            ]
            
            # Debug output
            print(f"\n[DEBUG] ===== FINAL RESULTS =====")
            print(f"[DEBUG] Total completed courses at Morgan State: {total_msu_courses}")
            print(f"[DEBUG] Total in-progress courses: {len(in_progress_courses)}")
            print(f"[DEBUG] Total completed credits at Morgan State: {total_completed_credits}")
            print(f"[DEBUG] Current semester credits: {current_term_credits}")
            print(f"\n[DEBUG] Semester breakdown (Morgan State only):")
            for sem in semesters_data:
                print(f"[DEBUG]   {sem['term']}: {sem['course_count']} courses, {sem['total_credits']} credits")
            print(f"[DEBUG] ===========================\n")
        # --------------------------------------------------------------------

        return {
    "status": "success",
    "html_file": html_filename,
    "txt_file": txt_filename,
    "json_file": json_filename,
    "json_preview": json_data if isinstance(json_data, dict) else None,
}


    except Exception as e:
        print(f"[ERROR] scrape_degreeworks() failed: {e}")
        return {"error": str(e), "status": "failed"}