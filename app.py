from flask import Flask, jsonify
from flask_pymongo import PyMongo
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from celery import Celery
import itertools

app = Flask(__name__)
app.debug = True
app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'
app.config['MONGO_URI'] = 'mongodb://localhost:27017/task'
mongo = PyMongo(app)
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)


@celery.task(bind=True)
def generate_distances(self):
    task_id = self.request.id
    body = {
        "status": "running",
        "task_id": task_id
    }

    job_id = mongo.db.job.insert_one(body).inserted_id
    points, links = start_job()

    mongo.db.job.find_one_and_update({"_id": job_id}, {"$set": {"status": "done"}})

    result = {
        "data": {
            "points": points,
            "links": links
        },
        "status": "done",
        "task_id": task_id
    }

    return result


@app.route('/api/calculateDistances', methods=['POST'])
def calculate_distances():
    task = generate_distances.delay()
    return jsonify(task_id=task.id, status='running')


@app.route('/api/links', methods=['GET'])
def get_links():
    points, links = start_job()
    return jsonify({'points': points, 'links': links})


@app.route('/api/getResult/<task_id>', methods=['GET'])
def get_result(task_id):
    task = generate_distances.AsyncResult(task_id)
    if task.state == 'PENDING':
        # job did not start yet
        response = {
            'data': task.info.get('data', []),
            'status': task.info.get('status', 'running'),
            'task_id': task.info.get('task_id', 0)
        }
    elif task.state != 'FAILURE':
        response = {
            'data': task.info.get('data', []),
            'status': task.info.get('status', 'running'),
            'task_id': task.info.get('task_id', 0)
        }
        if 'result' in task.info:
            response['result'] = task.info['result']
    else:
        # something went wrong in the background job
        response = {
            'data': task.info.get('data', []),
            'status': task.info.get('status', 'running'),
            'task_id': task.info.get('task_id', 0)
        }

    return jsonify(response)


def start_job():
    with open('locations.csv') as csv_file:
        locations = list(csv_file)[1:]
        points = create_points(locations)
        links = create_links(locations)

    return points, links


def create_links(csv_file):
    location_points = list(itertools.combinations(list(csv_file), 2))
    links = []

    for locations in location_points[1:]:
        location1 = locations[0].split(',')
        location2 = locations[1].split(',')

        print(str(locations))
        distance = geodesic((location1[1], location1[2].strip()), (location2[1], location2[2].strip())).meters
        links.append({"name": f'{location1[0]}-{location2[0]}', "distance": distance})

    return links


def create_points(locations):
    geolocator = Nominatim(user_agent="task")

    points = []
    for row in locations:
        row = row.split(',')
        location = geolocator.reverse(f'{row[1]}, {row[2].strip()}')
        points.append({"name": row[0], "address": location.address})

    return points


if __name__ == '__main__':
    app.run()
