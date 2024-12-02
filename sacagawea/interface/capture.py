import pyaudio
import wave
from vosk import Model, KaldiRecognizer  # change to deepspeech
import json
import threading
import queue


def list_audio_devices():
    p = pyaudio.PyAudio()
    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        print(f"device {i}: {info['name']}")
    p.terminate()


def transcribe_stream(q, rec):
    last_words = set()
    while True:
        data = q.get()
        if data is None:
            break
        if rec.AcceptWaveform(data):
            result = rec.Result()
            text = json.loads(result).get("text", "")
            words = text.split()
            for word in words:
                if word not in last_words:
                    print(word, end=" ", flush=True)
                    last_words.add(word)
        else:
            partial_result = rec.PartialResult()
            text = json.loads(partial_result).get("partial", "")
            words = text.split()
            for word in words:
                if word not in last_words:
                    print(word, end=" ", flush=True)
                    last_words.add(word)
    final_result = rec.FinalResult()
    text = json.loads(final_result).get("text", "")
    words = text.split()
    for word in words:
        if word not in last_words:
            print(word, end=" ", flush=True)
            last_words.add(word)
    print()


def capture_and_transcribe_audio(duration=10):
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

    if device_index is None:
        raise ValueError("blackhole device not found")

    stream = p.open(
        format=sample_format,
        channels=channels,
        rate=fs,
        input=True,
        input_device_index=device_index,
        frames_per_buffer=chunk,
    )

    print("recording and transcribing...")

    model = Model("models/vosk-model-en-us-0.42-gigaspeech")
    rec = KaldiRecognizer(model, fs)

    frames = []
    q = queue.Queue()
    transcribe_thread = threading.Thread(target=transcribe_stream, args=(q, rec))
    transcribe_thread.start()

    for _ in range(0, int(fs / chunk * duration)):
        try:
            data = stream.read(chunk, exception_on_overflow=False)
        except IOError as e:
            print(f"Error recording: {e}")
            continue
        frames.append(data)
        q.put(data)

    stream.stop_stream()
    stream.close()
    p.terminate()

    q.put(None)
    transcribe_thread.join()


def transcribe_audio(filename):
    model = Model("models/vosk-model-en-us-0.42-gigaspeech")
    wf = wave.open(filename, "rb")
    rec = KaldiRecognizer(model, wf.getframerate())

    while True:
        data = wf.readframes(4000)
        if len(data) == 0:
            break
        if rec.AcceptWaveform(data):
            result = rec.Result()
            text = json.loads(result).get("text", "")
            print(text)

    final_result = rec.FinalResult()
    text = json.loads(final_result).get("text", "")
    print(text)


if __name__ == "__main__":
    capture_and_transcribe_audio(duration=10)
