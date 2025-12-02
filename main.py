from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import PyPDF2
from gtts import gTTS
import os

app = FastAPI()

# Serve static files (your HTML/CSS/JS)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Create directories if they don't exist
os.makedirs("uploads", exist_ok=True)
os.makedirs("audio_output", exist_ok=True)


@app.get("/")
async def read_root():
    # Serve the main HTML page
    return FileResponse("static/index.html")


@app.post("/convert")
async def convert_pdf_to_audio(file: UploadFile = File(...)):
    # Save uploaded PDF
    pdf_path = f"uploads/{file.filename}"
    with open(pdf_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # Extract text from PDF, preserve line breaks between pages/paragraphs
    text = ""
    with open(pdf_path, "rb") as f:
        pdf_reader = PyPDF2.PdfReader(f)
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                # Keep the page's internal line breaks and add a blank line between pages
                text += page_text + "\n\n"

    # If nothing extracted, avoid crashing TTS
    cleaned_text = text.strip()
    if not cleaned_text:
        cleaned_text = "No readable text could be extracted from this PDF."

    # Convert text to audio
    audio_filename = file.filename.rsplit(".", 1)[0] + ".mp3"
    audio_path = f"audio_output/{audio_filename}"

    tts = gTTS(text=cleaned_text, lang="en")
    tts.save(audio_path)

    # Return the audio file info AND the full text
    return {
        "message": "Conversion successful!",
        "audio_file": audio_filename,
        "text": text,  # send the original with line breaks
    }


@app.get("/audio/{filename}")
async def get_audio(filename: str):
    audio_path = f"audio_output/{filename}"
    return FileResponse(audio_path, media_type="audio/mpeg")
