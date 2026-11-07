
import os
import uuid
import edge_tts

from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI(
    title="FastAPI Edge-TTS Audio Generator",
    description="Text to Speech Audio Generator",
    version="1.0.0"
)

# Audio output directory
OUTPUT_DIR = "audio"
os.makedirs(OUTPUT_DIR, exist_ok=True)

app.mount(
    "/audio",
    StaticFiles(directory=OUTPUT_DIR),
    name="audio"
)


@app.get("/")
async def home():
    return {
        "status": "success",
        "message": "FastAPI Edge-TTS Audio Generator is running",
        "docs": "/docs"
    }


@app.get("/voices")
async def get_voices():
    try:
        voices = await edge_tts.list_voices()

        return [
            {
                "name": voice["ShortName"],
                "gender": voice["Gender"],
                "locale": voice["Locale"]
            }
            for voice in voices
        ]

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@app.post("/generate")
async def generate_audio(
    text: str = Form(...),
    voice: str = Form("en-US-AriaNeural"),
    rate: str = Form("+0%"),
    volume: str = Form("+0%"),
    pitch: str = Form("+0Hz")
):

    if not text.strip():
        raise HTTPException(
            status_code=400,
            detail="Text cannot be empty"
        )

    filename = f"{uuid.uuid4().hex}.mp3"
    filepath = os.path.join(OUTPUT_DIR, filename)

    try:
        communicate = edge_tts.Communicate(
            text=text,
            voice=voice,
            rate=rate,
            volume=volume,
            pitch=pitch
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
            detail=str(e)
        )


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
￼Enter
