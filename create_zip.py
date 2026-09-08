import os
import zipfile

base_dir = "/Users/aakashtiru/Desktop/AI-Eng"
zip_filename = os.path.join(base_dir, "AI-Chatbot-Windows.zip")

files_to_include = [
    "server.py",
    "langchain_bot.py",
    "db.py",
    "requirements.txt",
    "README.md",
    "run_windows.bat",
    "AI_Chatbot_Architecture_Documentation.pdf"
]

static_files = [
    "static/index.html",
    "static/styles.css",
    "static/app.js"
]

with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
    for fname in files_to_include:
        fpath = os.path.join(base_dir, fname)
        if os.path.exists(fpath):
            zipf.write(fpath, arcname=fname)
    
    for sfname in static_files:
        sfpath = os.path.join(base_dir, sfname)
        if os.path.exists(sfpath):
            zipf.write(sfpath, arcname=sfname)

print(f"Zip created successfully at: {zip_filename} ({os.path.getsize(zip_filename)} bytes)")
