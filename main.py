from flask import Flask, request, json
import base64
from vosk import Model, KaldiRecognizer
import wave
import os
import io
from pydub import AudioSegment
from pydub.effects import normalize

app = Flask(__name__)
diretorio = os.path.abspath("vosk-model-small-pt-0.3")
model = Model(diretorio)

def improve_audio_quality(audio_data_base64):
    # Decode the base64 audio data
    audio_bytes = base64.b64decode(audio_data_base64)
    
    # Load the audio data into an AudioSegment object
    audio = AudioSegment.from_file(io.BytesIO(audio_bytes))
    
    # Apply audio processing effects to improve the quality
    audio = normalize(audio)
    # Export the processed audio data as a WAV file
    wav_bytes = audio.export(format="wav").read()
    
    # Encode the processed audio data as base64
    processed_audio_data_base64 = base64.b64encode(wav_bytes).decode('utf-8')
    
    return processed_audio_data_base64

@app.route('/transcribe', methods=['POST'])
def transcribe():
    audio_data = request.json['audio_data']
    improved_audio_data = improve_audio_quality(audio_data)
    audio_bytes = base64.b64decode(improved_audio_data)

   # Converte os dados de áudio para o formato MP3
    audio = AudioSegment.from_file(io.BytesIO(audio_bytes))
    
    audio.export("output.mp3", format="mp3")

    # Converte os dados de áudio para o formato WAV
    audio = AudioSegment.from_mp3("output.mp3")
    
    audio = audio.set_frame_rate(16000).set_channels(1)
    
    wav_bytes = audio.export(format="wav").read()

    wf = wave.open(io.BytesIO(wav_bytes), 'rb')
    rec = KaldiRecognizer(model, wf.getframerate())
    while True:
        data = wf.readframes(4096)
        if len(data) == 0:
            break
        rec.AcceptWaveform(data)
    result = rec.Result()
    transcription_data = json.loads(result)
    transcription_text = transcription_data['text']
    print(transcription_text)
    return {'transcription': transcription_text}
if __name__ == '__main__':
    app.run()