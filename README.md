# geo_calculator

## steps to run the application
    1. run docker redis on default port: docker run -d -p 6379:6379 redis
    2. run docker mongo on default port:  docker run -d -p 27017-27019:27017-27019 --name mongodb mongo:4.0.4
    3. install the python dependencies: pip install -r requirements.txt
    4. run celery worker: celery -A app.celery worker  --loglevel=info
    5. run python app: python app.py
    
## Description
    geo calculation app that running jobs in the backround.
    you can check the job by calling the get result API,
    where you could see if it still running or done with re result
    the task save in the mongo db
    
## API
    start calculation: curl --location --request POST 'http://localhost:5000/api/calculateDistances'
    get result: curl --location --request GET 'http://localhost:5000/api/getResult/{task_id}'