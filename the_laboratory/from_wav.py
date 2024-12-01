# converts from persian to english using vosk and deep_translator
# todo: time stamp for each sentence

import wave
import json
from vosk import Model, KaldiRecognizer
from deep_translator import GoogleTranslator

model_path = "models/vosk-model-small-fa-0.42"

model = Model(model_path)

# should be 16000 Hz 16-bit PCM
wf = wave.open("test.wav", "rb")

recognizer = KaldiRecognizer(model, wf.getframerate())

translator = GoogleTranslator(source='auto', target='en')

with open("leslie.txt", "w") as output_file:
    while True:
        data = wf.readframes(4000)
        if len(data) == 0:
            break
        if recognizer.AcceptWaveform(data):
            result = recognizer.Result()
            try:
                result_json = json.loads(result)
                print("raw result:", result_json)
                if 'text' in result_json:
                    cleaned_text = result_json['text'].replace('\u200c', '')
                    translated_text = translator.translate(cleaned_text)
                    output_file.write(f"English: {translated_text}\n")
                else:
                    print("no 'text' key in partial result")
            except json.JSONDecodeError:
                print("error decoding the JSON result")

    final_result = recognizer.FinalResult()
    try:
        final_result_json = json.loads(final_result)
        print("final result:", final_result_json)
        if 'text' in final_result_json:
            cleaned_text = final_result_json['text'].replace('\u200c', '')
            translated_text = translator.translate(cleaned_text)
            output_file.write(f"{translated_text}\n")
        else:
            print("no 'text' key in final result")
    except json.JSONDecodeError:
        print("json decode error")

print("done")