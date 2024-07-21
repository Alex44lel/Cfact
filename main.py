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
from typing import List, Optional
import json
from pydantic import BaseModel, Field
from flask import Flask, jsonify, request
from flask_cors import CORS
from multion.client import MultiOn
from dotenv import load_dotenv


load_dotenv()


if not hasattr(np, 'NAN'):
    np.NAN = float('nan')


class Cfact:
    def __init__(self):

        self.app = Flask(__name__)
        CORS(self.app, resources={r"/*": {"origins": "*"}})

        self.latest_fact_check_result = None

        self.groq = Groq()
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 16000
        self.CHUNK = 1024
        self.RECORD_SECONDS = 30
        self.WAVE_OUTPUT_FILENAME = "output.wav"

        self.audio_queue = queue.Queue()
        self.processesd_audio_queue = queue.Queue()
        self.stop_flag = threading.Event()
        # print(torch.device("cuda" if torch.cuda.is_available() else "cpu"))

        self.diarization_pipeline = Pipeline.from_pretrained(
            'pyannote/speaker-diarization-3.1', use_auth_token=os.getenv('HUGGING_FACE_TOKEN')).to(torch.device("cuda" if torch.cuda.is_available() else "cpu"))

    def record_audio(self):
        p = pyaudio.PyAudio()
        stream = p.open(format=self.FORMAT, channels=self.CHANNELS, rate=self.RATE,
                        input=True, frames_per_buffer=self.CHUNK)
        print('Recording...')
        chunk_counter = 0

        while not self.stop_flag.is_set():

            frames = []
            for _ in range(0, int(self.RATE / self.CHUNK * self.RECORD_SECONDS)):
                if self.stop_flag.is_set():
                    break
                data = stream.read(self.CHUNK)
                frames.append(data)

            self.audio_queue.put(frames)
            # save file chunk as wav file
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

    def transcrive_audio(self):
        chunk_counter = 0
        addSpeakersToTranscrip = AddSpeakersToTranscrip(self.RECORD_SECONDS)
        while not self.stop_flag.is_set():
            try:
                frames = self.audio_queue.get(timeout=1)
                print("Audio queue: ", self.audio_queue)
                print('proscessing new frame...\n')
                # create temporary wav file in memory
                with io.BytesIO() as wav_buffer:
                    with wave.open(wav_buffer, 'wb') as wf:
                        wf.setnchannels(self.CHANNELS)
                        wf.setsampwidth(
                            pyaudio.PyAudio().get_sample_size(self.FORMAT))
                        wf.setframerate(self.RATE)
                        wf.writeframes(b''.join(frames))
                    wav_buffer.seek(0)
                    print('INIT GROQ')
                    transcription = self.groq.audio.transcriptions.create(
                        file=("audio.wav", wav_buffer.read()),
                        model="whisper-large-v3",
                        # prompt="Specify context or spelling",  # Optional
                        response_format="verbose_json",  # Optional
                        language="en",  # Optional
                        temperature=0.0  # Optional
                    )
                    print('END GROQ')

                    wav_buffer.seek(0)
                    waveform, sample_rate = torchaudio.load(wav_buffer)
                    print('INIT DITARIZATION')
                    diarization_result = self.diarization_pipeline(
                        {"waveform": waveform, "sample_rate": sample_rate})
                    print('INIT DITARIZATION')

                    final_result = addSpeakersToTranscrip.diarize_text(
                        transcription, diarization_result, waveform, sample_rate, chunk_counter)
                    print("\nRESULT:\n")
                    formated_result = ''

                    if len(final_result) == 1 and final_result[0][2] == ' Thank you.':
                        print("No text to process")
                        continue
                    else:
                        for seg, spk, sent in final_result:
                            line = f'start:{seg.start:.2f} end:{seg.end:.2f} speaker:{spk} speaker_voice:{sent}'
                            formated_result = formated_result + line + '\n'

                        print("FORMATED RESULT: ",
                              formated_result)
                        self.processesd_audio_queue.put(formated_result)

                    wav_buffer.seek(0)
                    wav_buffer.truncate(0)
                    chunk_counter += 1

            except queue.Empty:
                # print("No audio data in queue")
                pass

            except Exception as e:
                print("Error getting transcription:", e)
                traceback.print_exc()

    def ask_llama_for_fact(self, text):
        class Fact(BaseModel):
            """
            A fact analized by the model
            """
            start: float = Field(description="The start time of the segment")
            end: float = Field(description="The end time of the segment")
            fact_state: int = Field(
                description="Return 1 if the fact is incorrect, 2 if correct and  0 if you can not deny the fact nor confirm it")
            speaker: str = Field(description="The speaker name")
            fact: str = Field(
                description="The fact (keep it short, a few words)")
            fact_correction: str = Field(
                description="The correction or the justification of why you can not answer(keep it short, a few words).")

        class Fact_check_results(BaseModel):
            """
            The fact check result
            """
            facts: List[Fact]

        facts_extracted = self.groq.chat.completions.create(

            messages=[
                {
                    "role": "user",
                    "content": f"Extract the facts from this text: {text}. If there are no facts return NONE",
                },
                {
                    "role": "system",
                    "content": f"""
                        Extract all the facts (even if they are wrong) from a text. Ignore things that are not facts in a debate.
                        Return one line per fact with the following format (EVEN IF THE FACT IS WRONG OR IT LOOKS LIKE AN OPINION):
                        fact: [fact]
                        Do not include meta-information such as:

                        -Details about speakers (e.g., names, speaking times)
                        -Information about the current conversation or testing process
                        -Observations about the text itself or lack of facts

                        Focus only on extracting substantive claims or statements about the world, history, science, or any topic being discussed, regardless of their accuracy.
                        If there are no substantive facts to extract, return: NONE
                    """
                    # Pass the json schema to the model. Pretty printing improves results.
                },
            ],

            model="llama3-70b-8192",
            temperature=0,
            # Streaming is not supported in JSON mode
            stream=False,
            # Enable JSON mode by setting the response format
        )
        print(facts_extracted.choices[0].message.content)

        if (facts_extracted.choices[0].message.content == 'NONE'):
            return None
        chat_completion = self.groq.chat.completions.create(

            messages=[
                {
                    "role": "user",
                    "content": "Fact check the following.  Only correct one fact at a time. Remember to think step by step, construct a chain of though ",
                },
                {
                    "role": "system",
                    "content": f"""Fact check the following text. Do it only for incorrect facts, ignore other things and facts that are right. Only check one fact at a time\n.
                    Please think step by step. If your fact correction explains why the fact is wrong, then fact state will always be 1
                    Text: {text}	\n
                    Facts: {facts_extracted.choices[0].message.content}

                    """
                    # Pass the json schema to the model. Pretty printing improves results.
                    f" The JSON object must use the schema: {json.dumps(Fact_check_results.model_json_schema(), indent=2)}",
                },
            ],
            model="mixtral-8x7b-32768",
            temperature=0,
            # Streaming is not supported in JSON mode
            stream=False,
            # Enable JSON mode by setting the response format
            response_format={"type": "json_object"},
        )

        res = Fact_check_results.model_validate_json(
            chat_completion.choices[0].message.content)

        frontend_data = []
        for fact in res.facts:
            print(fact.dict())
            frontend_data.append(fact.dict())

        json_data = json.dumps(frontend_data)
        return json_data

    def fact_check(self):
        while not self.stop_flag.is_set():
            try:
                # print("Checking for fact...: ",
                #       self.processesd_audio_queue.qsize())
                pass
                result = self.processesd_audio_queue.get(timeout=1)

                print("Fact checking result: ", result)
                result = self.ask_llama_for_fact(result)
                if result:
                    print(result)
                    self.latest_fact_check_result = result
                else:
                    print("NO FACTS FOUND")

            except queue.Empty:
                pass

            except Exception as e:
                print("Error getting fact checking:", e)
                traceback.print_exc()

    def start_api(self):

        @self.app.route('/api/fact-check', methods=['GET'])
        def get_fact_check():
            temp = self.latest_fact_check_result
            self.latest_fact_check_result = None
            if (temp == None):
                return "NO FACTS FOUND"
            return temp

        @self.app.route('/api/multion', methods=['POST'])
        def get_multion():
            data = request.json

            client = MultiOn(
                api_key=os.getenv('MULTION_API_KEY'),
            )

            prompt = f"Using wikipidia, tell me if {data['fact']} is a real fact or not and explain"

            retrieve_response = client.retrieve(
                cmd=prompt,
                url="https://www.wikipedia.org/",
                fields=["objective", "explanation"]
            )

            print(retrieve_response)
            data = retrieve_response.data[0]["explanation"]
            return data

        self.app.run(port=5000)

    def start(self):

        record_thread = threading.Thread(target=self.record_audio)
        transcribe_thread = threading.Thread(target=self.transcrive_audio)
        fact_check_thread = threading.Thread(target=self.fact_check)
        api_thread = threading.Thread(target=self.start_api)
        record_thread.start()
        transcribe_thread.start()
        fact_check_thread.start()
        api_thread.start()

        try:
            while True:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("Stopping...")
            # os._exit(1)

            self.stop_flag.set()

        record_thread.join()
        transcribe_thread.join()
        fact_check_thread.join()
        print("Finished.")


# start program
c = Cfact()
c.start()
os._exit(1)
