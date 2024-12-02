from sacagawea.core.config import Config
from sacagawea.interface.capture import capture_and_transcribe_audio


class Runner:
    def __init__(self, config: Config):
        self.config = config

    def __str__(self) -> str:
        return f"{self.config}"

    def run(self):
        print("Starting Program")
        capture_and_transcribe_audio(self.config.from_code, self.config.to_code)
        print("Ending Program")
