from sacagawea.core.config import Config
from sacagawea.interface.capture import CaptureManager


class Runner:
    def __init__(self, config: Config):
        self.config = config
        self.capture_manager = CaptureManager()

    def __str__(self) -> str:
        return f"{self.config}"

    def run(self):
        print("Starting Program")
        self.capture_manager.configure(
            from_code=self.config.from_code,
            to_code=self.config.to_code,
            model=self.config.model,
        )
        self.capture_manager.start_capture(None)
        print("Ending Program")
