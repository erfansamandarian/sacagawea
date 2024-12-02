import argostranslate.package
import argostranslate.translate
import json
import pyaudio
import queue
import threading
import warnings
import wave

from lightning_whisper_mlx import LightningWhisperMLX

warnings.filterwarnings(
    "ignore", category=FutureWarning, module="stanza.models.tokenize.trainer"
)


def list_audio_devices():
    p = pyaudio.PyAudio()
    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        print(f"device {i}: {info['name']}")
    p.terminate()


def transcribe_stream(q, p):
    from_code = "ru"
    to_code = "en"

    argostranslate.package.update_package_index()
    available_packages = argostranslate.package.get_available_packages()
    package_to_install = next(
        filter(
            lambda x: x.from_code == from_code and x.to_code == to_code,
            available_packages,
        ),
        None,
    )
    if package_to_install:
        argostranslate.package.install_from_path(package_to_install.download())

    installed_languages = argostranslate.translate.get_installed_languages()
    from_lang = next(
        (lang for lang in installed_languages if lang.code == from_code), None
    )
    to_lang = next((lang for lang in installed_languages if lang.code == to_code), None)
    if from_lang and to_lang:
        translation = from_lang.get_translation(to_lang)
    else:
        translation = None

    buffer = b""
    while True:
        data = q.get()
        if data is None:
            break
        buffer += data
        if len(buffer) >= 44100 * 2 * 5:
            with wave.open("buffer.wav", "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
                wf.setframerate(44100)
                wf.writeframes(buffer[: 44100 * 2 * 5])
            whisper = LightningWhisperMLX(model="base", batch_size=12, quant=None)
            text = whisper.transcribe(audio_path="buffer.wav")["text"]
            try:
                text_json = json.loads(text)
                original_text = text_json["text"]
                print(original_text)
                if translation:
                    translated_text = translation.translate(original_text)
                    print(translated_text)
            except json.JSONDecodeError:
                print(text)
                if translation:
                    translated_text = translation.translate(text)
                    print(translated_text)
            buffer = buffer[44100 * 2 * 5 :]
            open("buffer.wav", "w").close()


def capture_and_transcribe_audio():
    chunk = 4096
    sample_format = pyaudio.paInt16
    channels = 1
    fs = 44100

    p = pyaudio.PyAudio()

    list_audio_devices()

    device_index = None
    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        if "BlackHole" in info["name"]:
            device_index = i
            break
        elif "MacBook Pro Microphone" in info["name"]:
            device_index = i

    stream = p.open(
        format=sample_format,
        channels=channels,
        rate=fs,
        input=True,
        frames_per_buffer=chunk,
        input_device_index=device_index,
    )

    q = queue.Queue()

    threading.Thread(target=transcribe_stream, args=(q, p)).start()

    try:
        while True:
            data = stream.read(chunk)
            q.put(data)
    except KeyboardInterrupt:
        pass

    q.put(None)
    stream.stop_stream()
    stream.close()
    p.terminate()
