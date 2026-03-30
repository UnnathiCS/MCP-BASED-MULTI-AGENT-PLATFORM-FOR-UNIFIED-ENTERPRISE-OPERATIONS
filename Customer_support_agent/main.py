from fastapi import FastAPI, UploadFile, File
from models import ITSupportRequest, ITSupportResponse
from agent import decide_action
from voice import VoiceProcessor
import shutil

app = FastAPI(title="Enterprise IT Support Agent")

voice_processor = VoiceProcessor()

@app.post("/it-support/text", response_model=ITSupportResponse)
def handle_text(req: ITSupportRequest):
    result = decide_action(req.message)

    return ITSupportResponse(
        ticket_id=req.ticket_id,
        decision=result["decision"],
        reason=result["reason"],
        answer=result.get("answer"),
        severity=result.get("severity")
    )

@app.post("/it-support/voice", response_model=ITSupportResponse)
def handle_voice(ticket_id: str, audio: UploadFile = File(...)):
    audio_path = f"temp_{audio.filename}"

    with open(audio_path, "wb") as buffer:
        shutil.copyfileobj(audio.file, buffer)

    text = voice_processor.transcribe(audio_path)
    result = decide_action(text)

    return ITSupportResponse(
        ticket_id=ticket_id,
        decision=result["decision"],
        reason=f"Voice input processed → {result['reason']}",
        answer=result.get("answer"),
        severity=result.get("severity")
    )
