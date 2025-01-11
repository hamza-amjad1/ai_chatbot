from google.cloud import speech_v1p1beta1 as speech
from pydub import AudioSegment
import os

def transcribe_audio(file_path):
    try:
        print(f"Transcribing audio from: {file_path}")
        
        # Convert OGG to WAV
        if file_path.endswith(".ogg"):
            wav_path = file_path.replace(".ogg", ".wav")
            audio = AudioSegment.from_ogg(file_path)
            audio = audio.set_sample_width(2)  # Set sample width to 16 bits
            audio.export(wav_path, format="wav")
            file_path = wav_path  # Update file path to the new WAV file

        # Initialize Google Speech-to-Text client
        client = speech.SpeechClient()
        with open(file_path, "rb") as audio_file:
            audio_content = audio_file.read()
        
        # Configure recognition settings
        audio = speech.RecognitionAudio(content=audio_content)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=48000,
            language_code="en-US",
        )

        # Send audio to Google Speech-to-Text
        response = client.recognize(config=config, audio=audio)
        if response.results:
            transcription = response.results[0].alternatives[0].transcript
            print(f"Transcription result: {transcription}")
            return transcription
        else:
            print("No transcription results.")
            return None
    except Exception as e:
        print(f"Error during transcription: {e}")
        return None
    finally:
        # Clean up temporary files
        if os.path.exists(file_path):
            os.remove(file_path)
