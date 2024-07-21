import numpy as np
from scipy.spatial.distance import cosine
import torch
from pyannote.audio.pipelines.speaker_verification import PretrainedSpeakerEmbedding
from pyannote.core import Segment, Annotation, Timeline


class AddSpeakersToTranscrip:

    def __init__(self):
        self.speaker_embeddings = {}
        self.embedding_model = PretrainedSpeakerEmbedding(
            "speechbrain/spkrec-ecapa-voxceleb",
            device=torch.device("cuda" if torch.cuda.is_available() else "cpu"))
        self.PUNC_SENT_END = ['.', '?', '!']

        self.number_of_speakers = 0
        
    
    def get_text_with_timestamp(self,transcribe_res):
        timestamp_texts = []
        for item in transcribe_res.segments:
            start = item['start']
            end = item['end']
            text = item['text']
            timestamp_texts.append((Segment(start, end), text))
        return timestamp_texts


    #ann is the diarization result
    def add_speaker_info_to_text(self,timestamp_texts, ann, audio_chunk, sample_rate, chunk_number):
        spk_text = []
        for seg, text in timestamp_texts:
            spk = ann.crop(seg).argmax()
            #extract audio chunk for the segment
            start_sample = int(seg.start * sample_rate)
            end_sample = int(seg.end * sample_rate)
            speaker_audio = audio_chunk[:, start_sample:end_sample]
            
            # Convert speaker_audio to a PyTorch tensor if it's not already
            if not isinstance(speaker_audio, torch.Tensor):
                speaker_audio = torch.from_numpy(speaker_audio).float()

            # Move the tensor to the appropriate device
            speaker_audio = speaker_audio.to(self.embedding_model.device)

            # Add a batch dimension and get the embedding
            print('EMBEDDING')
            embedding = self.embedding_model(speaker_audio[None])
            print('end EMBEDDING')

            # Check if the result is a PyTorch tensor or NumPy array
            if isinstance(embedding, torch.Tensor):
                embedding = embedding.cpu().numpy()
            elif isinstance(embedding, np.ndarray):
                pass  # It's already a NumPy array, no need to convert
            else:
                raise TypeError(f"Unexpected type for embedding: {type(embedding)}")

            #compute speaker embedding
            embedding = np.ravel(embedding)

            if self.speaker_embeddings:
                print('INIT COSINE')
                distances = [cosine(embedding, np.ravel(emb)) for emb in self.speaker_embeddings.values()]
                min_distance = min(distances)
                if  min_distance < 0.7:
                    matched_speaker = list(self.speaker_embeddings.keys())[distances.index(min_distance)]
                    # Update the embedding (moving average)
                    self.speaker_embeddings[matched_speaker] = 0.9 * self.speaker_embeddings[matched_speaker] + 0.1 * embedding
                    spk = matched_speaker

                else:
                    if(self.number_of_speakers < 2):
                        self.number_of_speakers += 1
                        spk = f"spk_{self.number_of_speakers}"
                        self.speaker_embeddings[spk] = embedding

                    else:
                        matched_speaker = list(self.speaker_embeddings.keys())[distances.index(min_distance)]
                        # Update the embedding (moving average)
                        self.speaker_embeddings[matched_speaker] = 0.9 * self.speaker_embeddings[matched_speaker] + 0.1 * embedding
                        spk = matched_speaker
            else:
                self.number_of_speakers += 1
                spk = f"spk_{self.number_of_speakers}"
                self.speaker_embeddings[spk] = embedding
            print('END COSINE')
            
            spk_text.append((seg, spk, text))

        return spk_text

    def merge_cache(self,text_cache):
        sentence = ''.join([item[-1] for item in text_cache])
        spk = text_cache[0][1]
        start = text_cache[0][0].start
        end = text_cache[-1][0].end
        return Segment(start, end), spk, sentence

    def merge_sentence(self,spk_text):
        merged_spk_text = []
        pre_spk = None
        text_cache = []
        for seg, spk, text in spk_text:
            if spk != pre_spk and pre_spk is not None and len(text_cache) > 0:
                merged_spk_text.append(self.merge_cache(text_cache))
                text_cache = [(seg, spk, text)]
                pre_spk = spk

            elif text and len(text) > 0 and text[-1] in self.PUNC_SENT_END:
                text_cache.append((seg, spk, text))
                merged_spk_text.append(self.merge_cache(text_cache))
                text_cache = []
                pre_spk = spk
            else:
                text_cache.append((seg, spk, text))
                pre_spk = spk

        if len(text_cache) > 0:
            merged_spk_text.append(self.merge_cache(text_cache))
        return merged_spk_text


    def diarize_text(self,transcribe_res, diarization_result, audio_chunk, sample_rate, chunk_number):
        timestamp_texts = self.get_text_with_timestamp(transcribe_res)
        spk_text = self.add_speaker_info_to_text(timestamp_texts, diarization_result, audio_chunk, sample_rate, chunk_number)
        res_processed = self.merge_sentence(spk_text)
        return res_processed


    def write_to_txt(self,spk_sent, file):
        with open(file, 'w') as fp:
            for seg, spk, sentence in spk_sent:
                line = f'{seg.start:.2f} {seg.end:.2f} {spk} {sentence}\n'
                fp.write(line)