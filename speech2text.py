import io
import os


# Imports the Google Cloud client library
from google.cloud import speech
from google.cloud.speech import enums
from google.cloud.speech import types


def read_audio_file(file_name):
    # Loads the audio into memory
    try:
        with io.open(file_name, 'rb') as audio_file:
            content = audio_file.read()
            return content
    except:
        # todo: switch to logging absl style
        print('File cannot be read')


def recognize_audio(content):
    audio = types.RecognitionAudio(content=content)
    return audio


def transcribe(audio):
    # Instantiates a client
    client = speech.SpeechClient()

    config = types.RecognitionConfig(
        encoding=enums.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code='en-US')

    # Detects speech in the audio file
    response = client.recognize(config, audio)

    return response


if __name__ == '__main__':
    file_name = os.path.join(
        os.path.dirname(__file__),
        'resources',
        'audio2.wav')
    audio = read_audio_file(file_name)
    response = transcribe(audio)

    for result in response.results:
        print('Transcript: {}'.format(result.alternatives[0].transcript))

