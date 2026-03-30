try:
    import whisper
    _WHISPER_AVAILABLE = True
except Exception:
    whisper = None
    _WHISPER_AVAILABLE = False


class VoiceProcessor:
    """Wrapper around Whisper ASR. If the `whisper` package is not installed
    we provide a harmless fallback that returns an empty transcription and
    prints a warning — suitable for demos where voice is optional.
    """

    def __init__(self):
        if not _WHISPER_AVAILABLE:
            print("Warning: openai-whisper is not installed. Voice features will be disabled.")
            self.model = None
        else:
            self.model = whisper.load_model("base")

    def transcribe(self, audio_path: str) -> str:
        if not _WHISPER_AVAILABLE or self.model is None:
            # Return empty string so downstream logic can continue in demos
            return ""

        result = self.model.transcribe(audio_path)
        return result.get("text", "")
