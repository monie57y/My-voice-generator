
import os
import uuid
import edge_tts

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

app = FastAPI(
    title="FastAPI Edge-TTS Audio Generator",
    description="Text to Speech Audio Generation Backend",
    version="1.0.0"
)

# Configuration
OUTPUT_DIR = "audio"
os.makedirs(OUTPUT_DIR, exist_ok=True)

app.mount(
    "/audio",
    StaticFiles(directory=OUTPUT_DIR),
    name="audio"
)


# Request Model
class TTSRequest(BaseModel):
    text: str = Field(..., min_length=1)
    voice: str = "en-US-AriaNeural"
    rate: str = "+0%"
    volume: str = "+0%"
    pitch: str = "+0Hz"


# Home Endpoint
@app.get("/")
async def home():
    return {
        "status": "online",
        "message": "FastAPI Edge-TTS Backend Running",
        "documentation": "/docs"
    }


# Get Available Voices
@app.get("/voices")
async def get_voices():
    try:
        voices = await edge_tts.list_voices()

        return {
            "success": True,
            "total": len(voices),
            "voices": [
                {
                    "name": v["ShortName"],
                    "gender": v["Gender"],
                    "locale": v["Locale"]
                }
                for v in voices
            ]
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# Generate Audio
@app.post("/generate")
async def generate_audio(request: TTSRequest):

    if not request.text.strip():
        raise HTTPException(
            status_code=400,
            detail="Text cannot be empty"
        )

    filename = f"{uuid.uuid4().hex}.mp3"
    filepath = os.path.join(OUTPUT_DIR, filename)

    try:
        communicate = edge_tts.Communicate(
            text=request.text,
            voice=request.voice,
            rate=request.rate,
            volume=request.volume,
            pitch=request.pitch
        )

        await communicate.save(filepath)

        return {
            "success": True,
            "message": "Audio generated successfully",
            "filename": filename,
            "audio_url": f"/audio/{filename}",
            "download_url": f"/download/{filename}"
        }

    except Exception as e:

        if os.path.exists(filepath):
            os.remove(filepath)

        raise HTTPException(
            status_code=500,
            detail=f"Audio generation failed: {str(e)}"
        )


# Download Generated MP3
@app.get("/download/{filename}")
async def download_audio(filename: str):

    if (
        os.path.basename(filename) != filename
        or not filename.endswith(".mp3")
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid filename"
        )

    filepath = os.path.join(OUTPUT_DIR, filename)

    if not os.path.isfile(filepath):
        raise HTTPException(
            status_code=404,
            detail="Audio file not found"
        )

    return FileResponse(
        filepath,
        media_type="audio/mpeg",
        filename=filename
    )


# Health Check
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "Edge-TTS"
    }
