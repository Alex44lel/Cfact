import pyaudio
import wave
from groq import Groq
from pyannote.audio import Pipeline
from utils import AddSpeakersToTranscrip
import torch
import threading
import torchaudio
import queue
import time
import os
import io
import numpy as np
import traceback


if not hasattr(np, 'NAN'):
    np.NAN = float('nan')

client = Groq()
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 1024
RECORD_SECONDS = 30
WAVE_OUTPUT_FILENAME = "output.wav"

audio_queue = queue.Queue()
stop_flag = threading.Event()

diarization_pipeline = Pipeline.from_pretrained('pyannote/speaker-diarization-3.1',use_auth_token='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')

def record_audio():
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
    print('Recording...')
    chunk_counter = 0

    while not stop_flag.is_set():
        
        frames = []
        for _ in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
            if stop_flag.is_set():
                break
            data = stream.read(CHUNK)
            frames.append(data)

        audio_queue.put(frames)
        #save file chunk as wav file
        # chunk_filename = f"./audios/chunk_{chunk_counter}.wav"
        # with wave.open(chunk_filename, 'wb') as wf:
        #     wf.setnchannels(CHANNELS)
        #     wf.setsampwidth(p.get_sample_size(FORMAT))
        #     wf.setframerate(RATE)
        #     wf.writeframes(b''.join(frames))
        # print(f"Chunk {chunk_counter} saved")
        # chunk_counter += 1
    stream.stop_stream()
    stream.close()
    p.terminate()

def transcrive_audio():
    chunk_counter = 0

    addSpeakersToTranscrip = AddSpeakersToTranscrip()
    while not stop_flag.is_set():
        try:
            frames = audio_queue.get(timeout=1)
            print("Audio queue: ", audio_queue)
            print('proscessing new frame...\n')
            #create temporary wav file in memory
            with io.BytesIO() as wav_buffer:
                with wave.open(wav_buffer, 'wb') as wf:
                    wf.setnchannels(CHANNELS)
                    wf.setsampwidth(pyaudio.PyAudio().get_sample_size(FORMAT))
                    wf.setframerate(RATE)
                    wf.writeframes(b''.join(frames))
                wav_buffer.seek(0)

                print('INIT GROQ')
                transcription = client.audio.transcriptions.create(
                    file=("audio.wav", wav_buffer.read()),
                    model="whisper-large-v3",
                    #prompt="Specify context or spelling",  # Optional
                    response_format="verbose_json",  # Optional
                    language="en",  # Optional
                    temperature=0.0  # Optional
                )
                print('END GROQ')
                
                
                wav_buffer.seek(0)
                waveform, sample_rate = torchaudio.load(wav_buffer)
                print('INIT DITARIZATION')
                diarization_result = diarization_pipeline({"waveform": waveform, "sample_rate": sample_rate})
                print('INIT DITARIZATION')

                final_result = addSpeakersToTranscrip.diarize_text(transcription, diarization_result, waveform, sample_rate, chunk_counter)

                print("\nRESULT:\n")
                formated_result = ''
                for seg, spk, sent in final_result:
                    line = f'{seg.start:.2f} {seg.end:.2f} {spk} {sent}'
                    formated_result = formated_result + line + '\n'

                print(formated_result)
                wav_buffer.seek(0)
                wav_buffer.truncate(0)
                chunk_counter += 1


        except queue.Empty:
            #print("No audio data in queue")
            pass
        
        except Exception as e:
            print("Error getting transcription:", e)
            traceback.print_exc()


record_thread = threading.Thread(target=record_audio)
transcribe_thread = threading.Thread(target=transcrive_audio)
record_thread.start()
transcribe_thread.start()

try:
    while True:
        time.sleep(0.1)
except KeyboardInterrupt:
    print("Stopping...")
    stop_flag.set()

record_thread.join()
transcribe_thread.join()

print("Finished.")

