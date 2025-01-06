import argostranslate.package
import argostranslate.translate
import json
import pyaudio
import queue
import subprocess
import warnings
import wave
import asyncio
from concurrent.futures import ThreadPoolExecutor
from lightning_whisper_mlx import LightningWhisperMLX

warnings.filterwarnings(
    "ignore", category=FutureWarning, module="stanza.models.tokenize.trainer"
)


def list_audio_devices():
    p = pyaudio.PyAudio()
    info_list = []
    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        info_list.append((i, info["name"]))
    p.terminate()
    return info_list


class SpeechManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self.queue = queue.Queue()
        self.running = False

    async def start_thread(self):
        if self.running:
            return
        self.running = True
        loop = asyncio.get_event_loop()
        self.thread = loop.run_in_executor(None, self._speech_worker)

    async def stop_thread(self):
        self.running = False
        if self.queue:
            while not self.queue.empty():
                try:
                    self.queue.get_nowait()
                except queue.Empty:
                    pass
            self.queue.put(None)
        if self.thread:
            await self.thread

    def _speech_worker(self):
        while self.running:
            try:
                text = self.queue.get(timeout=0.5)
                if text is None or not self.running:
                    break
                subprocess.run(["say", text], check=True)
            except queue.Empty:
                continue
            except subprocess.SubprocessError as e:
                print(f"Speech Error ({type(e).__name__}): {str(e)}")
            finally:
                try:
                    self.queue.task_done()
                except ValueError:
                    pass

    def say(self, text):
        if self.running:
            self.queue.put(text)


speech_manager = SpeechManager()


class CaptureManager:
    def __init__(self):
        self.from_code = None
        self.to_code = None
        self.model = None
        self.running = False
        self.stream = None
        self.p = None
        self.q = None
        self.speak_enabled = True
        self.speech_manager = speech_manager

    def configure(self, from_code, to_code, model):
        self.from_code = from_code
        self.to_code = to_code
        self.model = model

    async def start_capture(self, signal):
        if self.running:
            return

        self.running = True
        self.p = pyaudio.PyAudio()
        self.q = queue.Queue()

        chunk = 4096
        sample_format = pyaudio.paInt16
        channels = 1
        fs = 44100

        devices = list_audio_devices()
        device_index = None
        for idx, name in devices:
            if "BlackHole" in name:
                device_index = idx
                break
            elif "MacBook Pro Microphone" in name:
                device_index = idx

        self.stream = self.p.open(
            format=sample_format,
            channels=channels,
            rate=fs,
            input=True,
            frames_per_buffer=chunk,
            input_device_index=device_index,
        )

        loop = asyncio.get_event_loop()
        self.transcribe_task = loop.run_in_executor(None, self._transcribe_wrapper)
        self.process_task = loop.create_task(self._process_transcription(signal))

    def _transcribe_wrapper(self):
        chunk = 4096
        try:
            while self.running:
                data = self.stream.read(chunk)
                self.q.put(data)
        except Exception as e:
            print(f"Capture Error: {str(e)}")
        finally:
            self.q.put(None)

    async def _process_transcription(self, signal):
        buffer = b""
        while self.running:
            try:
                data = await asyncio.get_event_loop().run_in_executor(None, self.q.get)
                if data is None:
                    break

                buffer += data
                if len(buffer) >= 44100 * 2 * 5:
                    with wave.open("buffer.wav", "wb") as wf:
                        wf.setnchannels(1)
                        wf.setsampwidth(self.p.get_sample_size(pyaudio.paInt16))
                        wf.setframerate(44100)
                        wf.writeframes(buffer[: 44100 * 2 * 5])
                    whisper = LightningWhisperMLX(
                        model=self.model, batch_size=12, quant=None
                    )
                    text = whisper.transcribe(audio_path="buffer.wav")["text"]

                    if text.strip():
                        translated = await asyncio.get_event_loop().run_in_executor(
                            None, self._translate_text, text
                        )
                        if signal:
                            signal.emit(text, translated)
                        if self.speak_enabled:
                            self.speech_manager.say(translated)

                    buffer = buffer[44100 * 2 * 5 :]
                    open("buffer.wav", "w").close()
            except Exception as e:
                print(f"Processing Error: {str(e)}")

    def _translate_text(self, text):
        try:
            text_json = json.loads(text)
            text = text_json["text"]
        except json.JSONDecodeError:
            pass

        argostranslate.package.update_package_index()
        available_packages = argostranslate.package.get_available_packages()
        package_to_install = next(
            filter(
                lambda x: x.from_code == self.from_code and x.to_code == self.to_code,
                available_packages,
            ),
            None,
        )
        if package_to_install:
            argostranslate.package.install_from_path(package_to_install.download())

        installed_languages = argostranslate.translate.get_installed_languages()
        from_lang = next(
            (lang for lang in installed_languages if lang.code == self.from_code), None
        )
        to_lang = next(
            (lang for lang in installed_languages if lang.code == self.to_code), None
        )

        if from_lang and to_lang:
            translation = from_lang.get_translation(to_lang)
            return translation.translate(text)
        return text

    async def stop_capture(self):
        self.running = False

        await self.speech_manager.stop_thread()

        if self.stream:
            self.stream.stop_stream()
            self.stream.close()

        if self.q:
            self.q.put(None)

        if self.transcribe_task:
            await self.transcribe_task
        if self.process_task:
            await self.process_task

        if self.p:
            self.p.terminate()

        self.stream = None
        self.p = None
        self.transcribe_task = None
        self.process_task = None
        self.q = None

        await self.speech_manager.start_thread()
