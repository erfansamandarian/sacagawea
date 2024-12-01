from sacagawea.core.config import Config

class Runner:
    def __init__(self, config: Config):
        self.config = config

    def __str__(self) -> str:
        return f"{self.config}"

    def run(self):
        print(f"model: {self.config.model}")