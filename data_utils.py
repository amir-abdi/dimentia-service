import requests
import json
import random

import constants
from constants import db_url
from text2speech import generate_speech
from logger import logger
import os


def random_question_id():
    json_query = '''{
            Questions {
                id
            }
          }'''

    questions = call_db(json_query)
    if questions is not None:
        questions = questions['Questions']
    else:
        return "Error on calling query_db"

    ids = []
    for q in questions:
        ids.append(q['id'])
    logger.info('question ids', ids)

    randi = random.randint(0, len(ids) - 1)
    return ids[randi]


def augment_question_with_voice(question):
    logger.info(question)
    logger.info('Augmenting question: %s', question['text'])
    speech = generate_speech(question['text'])
    # logger.info('speach %s', str(speech))
    number = random.randint(0, 10000000000)
    filename = '{}.mp3'.format(str(number))

    with open(os.path.join(constants.downloads_dir, filename), 'wb') as out:
        # Write the response to the output file.
        out.write(speech)
        logger.info('Audio content written to file %s', filename)

    question['speech'] = filename
    logger.info('question after speech %s', str(question))
    return question


def call_db(query, qtype='query'):
    params = {'Content-Type': 'application/json'}
    json_query = {
        'query': qtype + query
    }
    logger.info('Quering DB with %s', str(json_query))
    try:
        response = requests.post(db_url, params=params, json=json_query)
        print('status_code:', response.status_code)
        if response.status_code == 200:
            response = json.loads(response.text)
            response = response['data']
            return response
        else:
            logger.exception('Error:{}, {}, {}'.format(response.status_code, response.text, response.content))
            return None
    except Exception as e:
        logger.exception('[Errno {}'.format(e))
        return None


def sum_scores(scores):
    logger.info('sum_scores: %s', scores)
    sum = 0
    for s in scores:
        sum += s['score']
    logger.info('sum_scores: %s', sum)
    return sum


def generate_report(patientId, today_score):

    pass


def calculate_score(question_id, answer):
    return 12

