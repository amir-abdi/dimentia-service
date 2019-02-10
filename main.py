#!/usr/local/bin/python3

from flask import Flask
from flask import request as freq
from flask import make_response
from flask import send_from_directory
import json
import os
import datetime

from speech2text import read_audio_file, transcribe, recognize_audio
from text2speech import generate_speech
from constants import db_url
import constants
from data_utils import random_question_id, augment_question_with_voice, call_db, generate_report, sum_scores
from data_utils import calculate_score
from logger import logger

app = Flask(__name__)


@app.route('/')
def hello():
    """Return a friendly HTTP greeting."""
    return 'Dementia Backend Service for XDHacks 2019 - Team Demies'


@app.errorhandler(500)
def server_error(e):
    logger.exception('An error occurred during a request.')
    return """
    An internal error occurred: <pre>{}</pre>
    See logs for full stacktrace.
    """.format(e), 500


@app.route('/speach/v1.0/toText', methods=['POST'])
def voice2text_endpoint():
    logger.info('voice2text_endpoint')
    data = freq.data

    # file_name = os.path.join(
    #     os.path.dirname(__file__),
    #     'resources',
    #     'audio2.wav')

    # content = read_audio_file(file_name)
    audio = recognize_audio(data)
    response = transcribe(audio)
    #
    final_response = ''
    for result in response.results:
        logger.info('Transcript: {}'.format(result.alternatives[0].transcript))
        final_response += 'Transcript: {}'.format(result.alternatives[0].transcript)

    return final_response


@app.route('/speach/v1.0/toVoice', methods=['POST'])
def text2voice():
    logger.info('voice2text_endpoint')
    data = freq.data
    speech = generate_speech(data)

    response = make_response(speech, 200)
    # response = app.response_class(
    #     response=json.dumps(speech),
    #     status=200,
    #     mimetype='application/json'
    # )
    return response


@app.route('/data/v1.0/getQuestion', methods=['Get'])
def getQuestion():
    logger.info('getQuestion endpoint')

    randid = random_question_id()
    try:
        json_query_id = ''' {
                            Questions(where: {id: {_eq: %i }}) { 
                                id, text, image, type, patientId
                            }
                        }''' % randid

        logger.info(json_query_id)
        question = call_db(json_query_id)

        # question = requests.post(db_url, params=params, json=json_query_id)
        # question = json.loads(question.text)['Questions'][0]
        question = question['Questions'][0]
        print(question)
        logger.info('question %s', str(question))
        # return make_response(response_id, 200)

        question = augment_question_with_voice(question)
        # response = make_response(question)
        # return response
        return json.dumps(question)
        # return response_text
    except Exception as e:
        logger.exception(e)
        return '[Errno {}'.format(e)


@app.route('/data/v1.0/storeAnswer', methods=['POST'])
def storeAnswer():
    logger.info('storeAnswer endpoint')
    data = freq.json
    logger.info('data %s %s', type(data), data)
    if data is None:
        return make_response("No data in the POST request", 400)

    date = datetime.date.today()

    score = calculate_score(data['questionId'], data['answer'])

    query = ''' { insert_Answers(
            objects: [
              {
                questionId: %i,
                patientId: %i,
                score: %i,
                date: "%s"
                answer: "%s"
              }
            ]
          ) {
            returning {
              id
              score
            }
          }
        }''' % (data['questionId'], data['patientId'], score, date, data['answer'])

    logger.info('query %s', query)
    response = call_db(query, 'mutation')
    logger.info('response %s', str(response))
    response = json.dumps(response)
    return response


@app.route('/download/<path:filename>', methods=['GET'])
def download(filename):
    downloads = os.path.join(app.root_path, constants.downloads_dir)
    logger.info('downloads directory: %s', downloads)
    logger.info('filename: %s', filename)
    return send_from_directory(directory=downloads, filename=filename)


@app.route('/data/v1.0/done', methods=['POST'])
def done():
    logger.info("Done endpoint is called")
    today = datetime.date.today()
    # print(today)
    data = freq.json
    patientId = data['patientId']
    query_date = ''' {
                                Answers (where: {date: {_eq: \"%s\" },
                                                patientId: {_eq: %i} }) { 
                                    score
                                }
                            }''' % (str(today), patientId)
    response = call_db(query_date)
    logger.info('Response %s', response)
    response = response['Answers']
    score = sum_scores(response)

    generate_report(patientId, score)
    return make_response("Done", 200)


if __name__ == '__main__':
    # This is used when running locally. Gunicorn is used to run the
    # application on Google App Engine. See entrypoint in app.yaml.
    app.run(host='127.0.0.1', port=5000, debug=True)

