import json

from random import choice

from locust import (
    HttpUser,
    SequentialTaskSet,
    TaskSet,
    task,
    between
)


HOST = "http://localhost:8000"
VOTING = 1


class DefVisualizer(TaskSet):

    @task
    def index(self):
        self.client.get("/visualizer/{0}/".format(VOTING))


class DefVoters(SequentialTaskSet):

    def on_start(self):
        with open('voters.json') as f:
            self.voters = json.loads(f.read())
        self.voter = choice(list(self.voters.items()))

    @task
    def login(self):
        username, pwd = self.voter
        self.token = self.client.post("/authentication/login/", {
            "username": username,
            "password": pwd,
        }).json()

    @task
    def getuser(self):
        self.usr= self.client.post("/authentication/getuser/", self.token).json()
        print( str(self.user))

    @task
    def voting(self):
        headers = {
            'Authorization': 'Token ' + self.token.get('token'),
            'content-type': 'application/json'
        }
        self.client.post("/store/", json.dumps({
            "token": self.token.get('token'),
            "vote": {
                "a": "12",
                "b": "64"
            },
            "voter": self.usr.get('id'),
            "voting": VOTING
        }), headers=headers)


    def on_quit(self):
        self.voter = None

class CreateQuestion(SequentialTaskSet):

    def on_start(self):
        with open('questions.json') as f:
            self.questions = json.loads(f.read())
        self.question = choice(list(self.questions.items()))

    @task
    def login(self):
        self.token = self.client.post("/authentication/login/", {
            "username": "decide",
            "password": "decide2020",
        }).json()

    @task
    def create_question(self):
        response = self.client.get("/admin/voting/question/add/")
        csrftoken = response.cookies['csrftoken']
        desc, option = self.question
        headers = {
            'Authorization': 'Token ' + self.token.get('token'),
            'content-type': 'application/json',
            "X-CSRFToken": csrftoken
        }
        self.client.post("/admin/voting/question/add/", json.dumps({
            "token": self.token.get('token'),
            "question": {
                "desc" : desc,
                "options" : option
            }
        }), headers=headers)

    def on_quit(self):
        self.voter = None


class CreateQuestionOrder(SequentialTaskSet):

    def on_start(self):
        with open('question_orders.json') as f:
            self.question_orders = json.loads(f.read())
        self.question = choice(list(self.question_orders.items()))

    @task
    def login(self):
        self.token = self.client.post("/authentication/login/", {
            "username": "decide",
            "password": "decide2020",
        }).json()

    @task
    def create_question(self):
        response = self.client.get("/admin/voting/question/add/")
        csrftoken = response.cookies['csrftoken']
        desc, order_option = self.question
        headers = {
            'Authorization': 'Token ' + self.token.get('token'),
            'content-type': 'application/json',
            "X-CSRFToken": csrftoken
        }
        self.client.post("/admin/voting/question/add/", json.dumps({
            "token": self.token.get('token'),
            "question": {
                "desc" : desc,
                "order_options" : order_option
            }
        }), headers=headers)

    def on_quit(self):
        self.voter = None

class CreateVoting(SequentialTaskSet):

    def on_start(self):
        with open('question_orders.json') as f:
            self.question_orders = json.loads(f.read())
        self.question = choice(list(self.question_orders.items()))

        with open('votings.json') as f:
            self.votings=json.loads(f.read())

        self.voting_tuple = choice(list(self.votings.items()))

    @task
    def login(self):
        self.token = self.client.post("/authentication/login/", {
            "username": "decide",
            "password": "decide2020",
        }).json()

    @task
    def create_voting(self):
        response = self.client.get("/admin/voting/voting/add/")
        csrftoken = response.cookies['csrftoken']
        desc_question, order_option = self.question
        headers = {
            'Authorization': 'Token ' + self.token.get('token'),
            'content-type': 'application/json',
            "X-CSRFToken": csrftoken
        }

        self.json_auths=json.dumps({
            "token": self.token.get('token'),
            "auth": {
                "name" : 'localhost',
                "url" : 'http://localhost:8000',
                "me":True
            }})

        json_question_order=json.dumps({
            "token": self.token.get('token'),
            "question": {
                "desc" : desc_question,
                "order_options" : order_option
            }
        })

        nombre_votacion, votacion=self.voting_tuple
        name,desc,slug,voting_type=votacion

        self.client.post("/admin/voting/voting/add/", json.dumps({
            "token": self.token.get('token'),
            "voting": {
                "name" : name,
                "desc" : desc,
                "question": json_question_order,
                "auths":self.json_auths,
                "slug": slug,
                "voting_type":voting_type

            }
        }), headers=headers)

    def on_quit(self):
        self.voter = None

class Visualizer(HttpUser):
    host = HOST
    tasks = [DefVisualizer]
    wait_time = between(3,5)

class Voters(HttpUser):
    host = HOST
    tasks = [DefVoters]
    wait_time= between(3,5)

class Question(HttpUser):
    host = HOST
    tasks = [CreateQuestion]
    wait_time= between(3,5)

class QuestionOrder(HttpUser):
    host = HOST
    tasks = [CreateQuestionOrder]
    wait_time= between(3,5)

class Voting(HttpUser):
    host = HOST
    tasks = [CreateVoting]
    wait_time= between(3,5)