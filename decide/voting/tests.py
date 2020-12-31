import random
import itertools
from django.utils import timezone
from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework.test import APITestCase
from django.core.exceptions import ValidationError

from base import mods
from base.tests import BaseTestCase
from census.models import Census
from mixnet.mixcrypt import ElGamal
from mixnet.mixcrypt import MixCrypt
from mixnet.models import Auth
from voting.models import Voting, Question, QuestionOption, QuestionOrder


class VotingTestCase(BaseTestCase):

    def setUp(self):
        super().setUp()

    def tearDown(self):
        super().tearDown()

    def encrypt_msg(self, msg, v, bits=settings.KEYBITS):
        pk = v.pub_key
        p, g, y = (pk.p, pk.g, pk.y)
        k = MixCrypt(bits=bits)
        k.k = ElGamal.construct((p, g, y))
        return k.encrypt(msg)

    def create_voting(self):
        q = Question(desc='test question')
        q.save()
        for i in range(5):
            opt = QuestionOption(question=q, option='option {}'.format(i+1))
            opt.save()
        v = Voting(name='test voting', question=q)
        v.save()

        a, _ = Auth.objects.get_or_create(url=settings.BASEURL,
                                          defaults={'me': True, 'name': 'test auth'})
        a.save()
        v.auths.add(a)

        return v

    def create_order_voting(self):
        q = Question(desc='test ordering question')
        q.save()
        for i in range(5):
            opt = QuestionOrder(question=q, option='ordering option {}'.format(i+1), order_number='{}'.format(i+1))
            opt.save()
        v = Voting(name='test ordering voting', question=q)
        v.save()

        a, _ = Auth.objects.get_or_create(url=settings.BASEURL,
                                          defaults={'me': True, 'name': 'test auth'})
        a.save()
        v.auths.add(a)

        return v

    def create_voters(self, v):
        for i in range(100):
            u, _ = User.objects.get_or_create(username='testvoter{}'.format(i))
            u.is_active = True
            u.save()
            c = Census(voter_id=u.id, voting_id=v.id)
            c.save()

    def get_or_create_user(self, pk):
        user, _ = User.objects.get_or_create(pk=pk)
        user.username = 'user{}'.format(pk)
        user.set_password('qwerty')
        user.save()
        return user

    def test_voting_toString(self):
        v = self.create_voting()
        self.assertEquals(str(v), "test voting")
        self.assertEquals(str(v.question), "test question")
        self.assertEquals(str(v.question.options.all()[0]), "option 1 (2)")

    def test_update_voting_400(self):
        v = self.create_voting()
        data = {} #El campo action es requerido en la request
        self.login()
        response = self.client.put('/voting/{}/'.format(v.pk), data, format= 'json')
        self.assertEquals(response.status_code, 400)

    def store_votes(self, v):
        voters = list(Census.objects.filter(voting_id=v.id))
        voter = voters.pop()

        clear = {}
        for opt in v.question.options.all():
            clear[opt.number] = 0
            for i in range(random.randint(0, 5)):
                a, b = self.encrypt_msg(opt.number, v)
                data = {
                    'voting': v.id,
                    'voter': voter.voter_id,
                    'vote': { 'a': a, 'b': b },
                }
                clear[opt.number] += 1
                user = self.get_or_create_user(voter.voter_id)
                self.login(user=user.username)
                voter = voters.pop()
                mods.post('store', json=data)
        return clear

    def test_complete_voting(self):
        v = self.create_voting()
        self.create_voters(v)

        v.create_pubkey()
        v.start_date = timezone.now()
        v.save()

        clear = self.store_votes(v)

        self.login()  # set token
        v.tally_votes(self.token)

        tally = v.tally
        tally.sort()
        tally = {k: len(list(x)) for k, x in itertools.groupby(tally)}

        for q in v.question.options.all():
            self.assertEqual(tally.get(q.number, 0), clear.get(q.number, 0))

        for q in v.postproc:
            self.assertEqual(tally.get(q["number"], 0), q["votes"])

    def test_create_voting_from_api(self):
        data = {'name': 'Example'}
        response = self.client.post('/voting/', data, format='json')
        self.assertEqual(response.status_code, 401)

        # login with user no admin
        self.login(user='noadmin')
        response = mods.post('voting', params=data, response=True)
        self.assertEqual(response.status_code, 403)

        # login with user admin
        self.login()
        response = mods.post('voting', params=data, response=True)
        self.assertEqual(response.status_code, 400)

        data = {
            'name': 'Example',
            'desc': 'Description example',
            'question': 'I want a ',
            'question_opt': ['cat', 'dog', 'horse'],
            'question_ord': []
        }

        response = self.client.post('/voting/', data, format='json')
        self.assertEqual(response.status_code, 201)

    def test_create_ordering_voting_from_api(self):
        data = {'name': 'Example'}

        self.login()
        response = mods.post('voting', params=data, response=True)
        self.assertEqual(response.status_code, 400)

        data = {
            'name': 'Example',
            'desc': 'Description example',
            'question': 'I want a ',
            'question_opt': [],
            'question_ord': ['cat', 'dog', 'horse']
        }

        response = self.client.post('/voting/', data, format='json')
        self.assertEqual(response.status_code, 201)

    def test_update_voting(self):
        voting = self.create_voting()

        data = {'action': 'start'}
        #response = self.client.post('/voting/{}/'.format(voting.pk), data, format='json')
        #self.assertEqual(response.status_code, 401)

        # login with user no admin
        self.login(user='noadmin')
        response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
        self.assertEqual(response.status_code, 403)

        # login with user admin
        self.login()
        data = {'action': 'bad'}
        response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
        self.assertEqual(response.status_code, 400)

        # STATUS VOTING: not started
        for action in ['stop', 'tally']:
            data = {'action': action}
            response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.json(), 'Voting is not started')

        data = {'action': 'start'}
        response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), 'Voting started')

        # STATUS VOTING: started
        data = {'action': 'start'}
        response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), 'Voting already started')

        data = {'action': 'tally'}
        response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), 'Voting is not stopped')

        data = {'action': 'stop'}
        response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), 'Voting stopped')

        # STATUS VOTING: stopped
        data = {'action': 'start'}
        response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), 'Voting already started')

        data = {'action': 'stop'}
        response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), 'Voting already stopped')

        data = {'action': 'tally'}
        response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), 'Voting tallied')

        # STATUS VOTING: tallied
        data = {'action': 'start'}
        response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), 'Voting already started')

        data = {'action': 'stop'}
        response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), 'Voting already stopped')

        data = {'action': 'tally'}
        response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), 'Voting already tallied')


class VotingModelTestCase(BaseTestCase):

    def setUp(self):
        q1 = Question(desc='This is a test yes/no question', is_yes_no_question=True)
        q1.save()

        q2 = Question(desc='This is NOT a test yes/no question', is_yes_no_question=False)
        q2.save()

        q3 = Question(desc='This contain an order question', is_yes_no_question=False)
        q3.save()

        qo1 = QuestionOption(question = q2, option = 'Primera opcion')
        qo1.save()

        qo2 = QuestionOption(question = q2, option = 'Segunda opcion')
        qo2.save()

        qo3 = QuestionOption(question = q2, option = 'Tercera opcion')
        qo3.save()

        qord1 = QuestionOrder(question = q3, option = 'First Order')

        super().setUp()

    def tearDown(self):
        super().tearDown()

    def test_delete_when_unselect(self):
        q = Question.objects.get(desc='This is a test yes/no question')
        q.is_yes_no_question = False
        q.save()

        self.assertEquals(len(q.options.all()), 0)

    # don't save others YES/NO if it saves question with YES/NO question selected
    def test_duplicity_yes_and_no(self):
        q = Question.objects.get(desc='This is a test yes/no question')
        q.save()

        self.assertEquals(len(q.options.all()), 2)
        self.assertEquals(q.options.all()[0].question, q)
        self.assertEquals(q.options.all()[1].question, q)
        self.assertEquals(q.options.all()[0].option, 'YES')
        self.assertEquals(q.options.all()[1].option, 'NO')
        self.assertEquals(q.options.all()[0].number, 0)
        self.assertEquals(q.options.all()[1].number, 1)

    # add NO option before select YES/NO question and don't add this one
    def test_duplicity_yes(self):
        q = Question.objects.get(desc='This is a test yes/no question')
        qo = QuestionOption(question = q, number = 2, option = 'YES')
        qo.save()
        q.save()

        self.assertEquals(len(q.options.all()), 2)
        self.assertEquals(q.options.all()[0].question, q)
        self.assertEquals(q.options.all()[1].question, q)
        self.assertEquals(q.options.all()[0].option, 'YES')
        self.assertEquals(q.options.all()[1].option, 'NO')
        self.assertEquals(q.options.all()[0].number, 0)
        self.assertEquals(q.options.all()[1].number, 1)

    # add NO option before select YES/NO question and don't add this one
    def test_duplicity_no(self):
        q = Question.objects.get(desc='This is a test yes/no question')
        qo = QuestionOption(question = q, number = 2, option = 'NO')
        qo.save()
        q.save()

        self.assertEquals(len(q.options.all()), 2)
        self.assertEquals(q.options.all()[0].question, q)
        self.assertEquals(q.options.all()[1].question, q)
        self.assertEquals(q.options.all()[0].option, 'YES')
        self.assertEquals(q.options.all()[1].option, 'NO')
        self.assertEquals(q.options.all()[0].number, 0)
        self.assertEquals(q.options.all()[1].number, 1)

    # verify when selected YES/NO options that adds these
    def add_yes_no_question(self):
        q = Question.objects.get(desc='This is NOT a test yes/no question')
        q.is_yes_no_question = True
        q.save()

        self.assertEquals(len(q.options.all()), 2)
        self.assertEquals(q.options.all()[0].question, q)
        self.assertEquals(q.options.all()[1].question, q)
        self.assertEquals(q.options.all()[0].option, 'YES')
        self.assertEquals(q.options.all()[1].option, 'NO')
        self.assertEquals(q.options.all()[0].number, 0)
        self.assertEquals(q.options.all()[1].number, 1)

    # add some option before and don't add this one if YES/NO is selected
    def add_before_yes_no(self):
        q = Question.objects.get(desc='This is a test yes/no question')
        qo = QuestionOption(question = q, number = 2, option = 'Something')
        qo.save()
        q.save()

        self.assertEquals(len(q.options.all()), 2)
        self.assertEquals(q.options.all()[0].question, q)
        self.assertEquals(q.options.all()[1].question, q)
        self.assertEquals(q.options.all()[0].option, 'YES')
        self.assertEquals(q.options.all()[1].option, 'NO')
        self.assertEquals(q.options.all()[0].number, 0)
        self.assertEquals(q.options.all()[1].number, 1)

    # previous options are deleted when question is saved like YES/NO question
    def test_delete_previous_opt(self):
        q = Question.objects.get(desc='This is NOT a test yes/no question')
        q.is_yes_no_question = True
        q.save()

        self.assertEquals(len(q.options.all()), 2)
        self.assertEquals(q.options.all()[0].question, q)
        self.assertEquals(q.options.all()[1].question, q)
        self.assertEquals(q.options.all()[0].option, 'YES')
        self.assertEquals(q.options.all()[1].option, 'NO')
        self.assertEquals(q.options.all()[0].number, 0)
        self.assertEquals(q.options.all()[1].number, 1)

    # delete NO option, save and returns YES and NO option
    def test_delete_no_with_yes_no_selected(self):
        q = Question.objects.get(desc='This is a test yes/no question')
        qo = QuestionOption.objects.get(option = 'NO', question = q)
        QuestionOption.delete(qo)
        q.save()

        self.assertEquals(len(q.options.all()), 2)
        self.assertEquals(q.options.all()[0].question, q)
        self.assertEquals(q.options.all()[1].question, q)
        self.assertEquals(q.options.all()[0].option, 'YES')
        self.assertEquals(q.options.all()[1].option, 'NO')
        self.assertEquals(q.options.all()[0].number, 0)
        self.assertEquals(q.options.all()[1].number, 1)

    # delete YES option, save and returns YES and NO option
    def test_delete_yes_with_yes_no_selected(self):
        q = Question.objects.get(desc='This is a test yes/no question')
        qo = QuestionOption.objects.get(option = 'YES', question = q)
        QuestionOption.delete(qo)
        q.save()

        self.assertEquals(len(q.options.all()), 2)
        self.assertEquals(q.options.all()[0].question, q)
        self.assertEquals(q.options.all()[1].question, q)
        self.assertEquals(q.options.all()[0].option, 'YES')
        self.assertEquals(q.options.all()[1].option, 'NO')
        self.assertEquals(q.options.all()[0].number, 0)
        self.assertEquals(q.options.all()[1].number, 1)

    # question cannot contain 2 different options with the same "name"
    def test_duplicity_option(self):
        q = Question.objects.get(desc='This is NOT a test yes/no question')
        qo = QuestionOption(question = q, option = 'Primera opcion')
        qo.save()
        q.save()

        self.assertRaises(ValidationError)
        self.assertRaisesRegex(ValidationError,"Duplicated option, please checkout question options")
        self.assertEquals(len(q.options.all()), 3)

    # question cannot contain 2 different order with the same "name"
    def test_duplicity_order(self):
        q = Question.objects.get(desc='This is NOT a test yes/no question')
        qo = QuestionOrder(question = q, option = 'Primera opcion')
        qo.save()
        q.save()

        self.assertRaises(ValidationError)
        self.assertRaisesRegex(ValidationError,"Duplicated order, please checkout question order")
        self.assertEquals(len(q.options.all()), 3)
