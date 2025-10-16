from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from scraper2 import scrape_degreeworks
import html
import os
import json

app = FastAPI()

# ✅ Allow Android devices (and any frontend) to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can narrow this down later for security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message": "Morgan State Scraper API is running!"}

@app.get("/testwrite")
def test_write():
    test_html = "<html><body><p>Hello World</p></body></html>"
    return scrape_degreeworks(test_html)

@app.post("/scrape")
async def scrape(request: Request):
    data = await request.json()
    html_content = data.get("html")

    if not html_content:
        return JSONResponse({"error": "No HTML provided"}, status_code=400)

    # --- Decode twice, then interpret Unicode escapes ---
    try:
        cleaned_html = html_content.encode('utf-8').decode('unicode_escape')
        cleaned_html = html.unescape(cleaned_html)
    except Exception as e:
        cleaned_html = html.unescape(html_content)
        print("⚠️ Unicode decode fallback:", e)

    os.makedirs("testwrite", exist_ok=True)
    with open("testwrite/raw_received.html", "w", encoding="utf-8") as f:
        f.write(cleaned_html)

    print(f"✅ HTML received and decoded. Length: {len(cleaned_html)}")

    result = scrape_degreeworks(cleaned_html)
    return {"status": "success", "data": result}