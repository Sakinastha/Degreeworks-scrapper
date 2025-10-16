# DegreeWorks HTML Scraper API

This project is a simple API built with **FastAPI** that processes raw DegreeWorks HTML content, parses it using **Selectolax** and regular expressions, and outputs a structured JSON object representing a student's academic progress.

-----

## 💻 Project Files (Python Backend)

| File Name | Description |
| :--- | :--- |
| `server.py` | Defines the **FastAPI** application and API endpoints. Handles receiving and decoding the HTML input. |
| `scraper2.py` | Contains the core logic for scraping the HTML. It uses **Selectolax** to extract paragraph text and calls `json_convert.py` to structure the data. It also manages file saving for raw HTML, parsed text, and final JSON outputs. |
| `json_convert.py` | Contains the function `parse_degreeworks_txt`. This is the heavy lifting of the data conversion, using **regular expressions** to extract GPA, completed courses, and remaining requirements from the plain text and structure it into a Python dictionary (JSON). |

-----

## ⚙️ API Endpoints

The API is defined in `server.py` and offers the following endpoints:

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | Simple health check. Returns `{"message": "Morgan State Scraper API is running!"}`. |
| `GET` | `/testwrite` | A test endpoint to run the scraping logic with a minimal, hardcoded HTML string. Useful for quickly verifying file I/O and the scraper's basic functionality. |
| `POST` | `/scrape` | The main endpoint for submitting HTML content for scraping. It expects a JSON payload. |

### `/scrape` Endpoint Usage

The primary way to use the API is by sending a `POST` request to `/scrape`.

#### Request Body (JSON)

```json
{
  "html": "<html>...your raw DegreeWorks HTML content, likely escaped/encoded...</html>"
}
```

The server attempts to handle common encoding/escaping issues that might arise when sending large blocks of HTML within a JSON payload, first trying to decode it as a `unicode_escape` string before falling back to standard `html.unescape`.

#### Successful Response (JSON)

The response will contain the structured data, along with paths to the files saved on the server.

```json
{
  "status": "success",
  "data": {
    "status": "success",
    "paragraph_count": 42, 
    "html_file": "scraped_data/degreeworks_raw_20251016_123000.html",
    "txt_file": "scraped_data/degreeworks_paragraphs_20251016_123000.txt",
    "json_file": "scraped_data/degreeworks_data_20251016_123000.json",
    "json_preview": {
      "student_name": null, 
      "gpa": 3.85,
      "sections": [
        // ... structured academic data ...
      ]
    }
  }
}
```

-----

## 📊 Data Structure and Output

The final output is a structured JSON file (and a preview in the API response) following this schema:

```json
{
  
  "gpa": 3.85,         // Extracted using the pattern "Overall GPA X.XX"
  "sections": [
    {
      "name": "Major Requirements", // One of the predefined section headers
      "completed_courses": [
        {
          "course": "CMSC 101",
          "title": "Intro to Computing",
          "grade": "A",
          "credits": "3.00",
          "term": "Fall 2024"
        }
      ],
      "remaining_requirements": [
        "Take 1 more course from CMSC 300, MATH 320."
      ]
    }
  ]
}
```

### Key Logic in `json_convert.py`

  * **Sectioning:** The text is split using a predefined list of academic section headers (e.g., "Major Requirements", "Electives") via `text.find()` based on the order of the headers.
  * **Course Extraction:** Completed courses are extracted using a detailed regular expression that looks for patterns like `Course XXXX Title XXX Grade X Credits X.XX Term XXX`.
  * **Remaining Requirements:** Unmet requirements are extracted using the pattern `Still needed: [requirement text]`.

-----

## 🛠️ Installation and Setup

1.  **Dependencies:**
    Install the required Python libraries via `pip`:
    ```bash
    pip install fastapi uvicorn selectolax python-multipart
    ```
2.  **Run the API:**
    Start the server using `uvicorn`:
    ```bash
    uvicorn server:app --reload
    ```
    The API will be available at `http://127.0.0.1:8000/` (or similar).
3.  **File Output:**
    The scraper will automatically create a directory named **`scraped_data`** and save the raw HTML, plain text, and final JSON files there with a timestamped filename.

-----

## 📱 Android Frontend (Testing Contributor)

This repository includes associated Android files designed to facilitate **testing** of the DegreeWorks Scraper API.

The Android application is configured to:

  * Load a **static, test HTML string** into a `WebView` (instead of a live page).
  * Capture the `outerHTML` of this test content.
  * Send the captured test HTML via an **OkHttp POST request** to the `/scrape` endpoint on the server (e.g., `http://10.103.107.4:8000/scrape`).

This setup allows developers to quickly verify that the backend scraper is correctly parsing typical DegreeWorks structure and content.
