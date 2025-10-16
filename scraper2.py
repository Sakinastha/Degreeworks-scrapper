import os
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
        paragraphs = tree.css("p")

        if not paragraphs:
            print("[WARNING] No <p> tags found.")
            text_content = tree.text(separator="\n").strip()
        else:
            text_content = "\n\n".join([p.text(strip=True) for p in paragraphs])

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

        # --- Return summary to the API ---
        return {
            "status": "success",
            "paragraph_count": len(paragraphs),
            "html_file": html_filename,
            "txt_file": txt_filename,
            "json_file": json_filename,
            "json_preview": json_data if isinstance(json_data, dict) else None
        }

    except Exception as e:
        print(f"[ERROR] scrape_degreeworks() failed: {e}")
        return {"error": str(e), "status": "failed"}
