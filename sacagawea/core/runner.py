from sacagawea.core.config import Config
from sacagawea.interface.capture import capture_and_transcribe_audio
from whisper_mps import whisper


class Runner:
    def __init__(self, config: Config):
        self.config = config

    def __str__(self) -> str:
        return f"{self.config}"

    def run(self):
        print(f"model: {self.config.model}")

        capture_and_transcribe_audio()
