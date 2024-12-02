import pyaudio
import wave
from whisper_mps import whisper
import json
import threading
import queue


def list_audio_devices():
    p = pyaudio.PyAudio()
    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        print(f"device {i}: {info['name']}")
    p.terminate()


def transcribe_stream(q, p):
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
            text = whisper.transcribe("buffer.wav", model="base")
            if isinstance(text, dict):
                text_json = text
            else:
                text_json = json.loads(text)
            print(text_json["text"])
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
