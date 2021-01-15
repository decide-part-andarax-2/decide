import random
import itertools
import time
import os
import tarfile
import shutil

from django.utils import timezone
from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework.test import APITestCase
from django.core.exceptions import ValidationError
from django.contrib.staticfiles.testing import StaticLiveServerTestCase

from base import mods
from base.tests import BaseTestCase
from census.models import Census
from mixnet.mixcrypt import ElGamal
from mixnet.mixcrypt import MixCrypt
from mixnet.models import Auth
from voting.models import Voting, Question, QuestionOption, QuestionOrder

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

from parameterized import parameterized


class VotingTestCase(BaseTestCase):

    def setUp(self):
        super().setUp()

    def tearDown(self):
        if(os.path.exists("voting/results/")):
            shutil.rmtree('voting/results')
        super().tearDown()

    def encrypt_msg(self, msg, v, bits=settings.KEYBITS):
        pk = v.pub_key
        p, g, y = (pk.p, pk.g, pk.y)
        k = MixCrypt(bits=bits)
        k.k = ElGamal.construct((p, g, y))
        return k.encrypt(msg)

    @classmethod
    def create_auth(self):
        a, _ = Auth.objects.get_or_create(url=settings.BASEURL,
                                          defaults={'me': True, 'name': 'test auth'})
        a.save()
        return a

    @classmethod
    def create_question(self):
        q = Question(desc='test question')
        q.save()
        for i in range(5):
            opt = QuestionOption(question=q, option='option {}'.format(i+1))
            opt.save()
        return q

    @classmethod
    def create_ordered_question(self):
        q = Question(desc='test ordering question')
        q.save()
        for i in range(5):
            opt = QuestionOrder(question=q, option='ordering option {}'.format(i+1), order_number='{}'.format(i+1))
            opt.save()
        return q

    def create_voting(self):
        q = self.create_question()
        v = Voting(name='test voting', question=q, slug="prueba")
        v.save()

        a = self.create_auth()
        v.auths.add(a)

        return v

    def create_order_voting(self):
        q = self.create_ordered_question()
        v = Voting(name='test ordering voting', question=q)
        v.save()

        a = self.create_auth()
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

    @parameterized.expand([
        ["correct_voting", "test_voting", "description","slugprueba"],
        ["bad_slug", "test_voting1", "description1","slug!prueba1"],
        ["no_name", "", "description2","slugprueba2"],
        ["no_slug", "test_voting_3", "description3",""],
        ["no_question", "test_voting_4", "description4","slugprueba4"]
    ])
    def test_parametrizado(self, title, name, desc, slug):
        q = self.create_question()
        if title == "no_question":
            v = Voting(name=name, desc=desc, slug=slug)
        else:
            v = Voting(name=name, desc=desc, question=q, slug=slug)
        if not title == "correct_voting":
            with self.assertRaises(ValidationError):
                v.full_clean()
        else:
            v.save()
            self.assertIsNotNone(Voting.objects.get(name=name))

    @parameterized.expand([
        ["correct_question", "test_descripcion"],
        ["no_description", ""]
    ])
    def test_parametrizado_question(self, title, desc):
        q = Question(desc=desc)
        if title=="no_description":
            with self.assertRaises(ValidationError):
                q.full_clean()
        else:
            q.save()
            self.assertIsNotNone(Question.objects.get(desc=desc))

    @parameterized.expand([
        ["correct_question_option", "10", "option"],
        ["no_option", "11", ""]
    ])
    def test_parametrizado_question_option(self, title, number, option):
        question = self.create_question()
        qo = QuestionOption(question=question, number=int(number), option=option)
        if title=="no_option":
            with self.assertRaises(ValidationError):
                qo.full_clean()
        else:
            qo.save()
            self.assertIsNotNone(QuestionOption.objects.get(option=option))

    def test_question_invalid(self):
        q = Question(desc='')
        with self.assertRaises(ValidationError):
            q.full_clean()

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

    def test_postproc_voting_compressed(self):
        v = self.create_voting()
        self.create_voters(v)

        v.create_pubkey()
        v.start_date = timezone.now()
        v.save()

        self.store_votes(v)

        self.login()  # set token
        v.tally_votes(self.token)

        tally = v.tally
        tally.sort()
        tally = {k: len(list(x)) for k, x in itertools.groupby(tally)}

        self.assertTrue(os.path.exists("voting/results/results.tar"))
        tarfl = tarfile.open("voting/results/results.tar", "r")
        name = "voting/results/v" + str(v.id)  + "_" + v.slug + ".txt"
        self.assertTrue(name in tarfl.getnames())
        tarfl.close()

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
            'slug': 'example',
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
            'slug': 'example',
            'question': 'I want a ',
            'question_opt': [],
            'question_ord': ['cat', 'dog', 'horse']
        }

        response = self.client.post('/voting/', data, format='json')
        self.assertEqual(response.status_code, 201)

    def test_create_voting_absoluta(self):
        q1=Question(desc="Pregunta para votacion absoluta")
        q1.save()

        ord1 = QuestionOrder(question=q1, option="primera", order_number=2)
        ord1.save()
        ord2 = QuestionOrder(question=q1, option="segunda", order_number=1)
        ord2.save()

        v1=Voting(name="Votacion absoluta",question=q1,voting_type='ABSOLUTA')
        v1.save()

        self.assertEquals(Voting.objects.get(name="Votacion absoluta").voting_type, 'ABSOLUTA')

    def test_create_voting_relativa(self):
        q1=Question(desc="Pregunta para votacion relativa")
        q1.save()

        ord1 = QuestionOrder(question=q1, option="primera", order_number=2)
        ord1.save()
        ord2 = QuestionOrder(question=q1, option="segunda", order_number=1)
        ord2.save()

        v1=Voting(name="Votacion relativa",question=q1,voting_type='RELATIVA')
        v1.save()

        self.assertEquals(Voting.objects.get(name="Votacion relativa").voting_type, 'RELATIVA')

    def test_create_voting_default_type(self):
        q1=Question(desc="Pregunta para votacion sin tipo correcto")
        q1.save()

        ord1 = QuestionOrder(question=q1, option="primera", order_number=2)
        ord1.save()
        ord2 = QuestionOrder(question=q1, option="segunda", order_number=1)
        ord2.save()

        v1=Voting(name="Votacion tipo_inventado",question=q1)
        v1.save()

        self.assertEqual(Voting.objects.get(name="Votacion tipo_inventado").voting_type, "IDENTITY")

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

        qord1 = QuestionOrder(question = q3, option = 'First order')
        qord1.save()

        q=Question(desc="Esta es la descripcion")
        q.save()

        opt1=QuestionOption(question=q,option="opcion1")
        opt2=QuestionOption(question=q,option="opcion2")
        opt1.save()
        opt2.save()

        self.v=Voting(name="Votacion",question=q, slug="slug1")
        self.v.save()

        q2=Question(desc="Segunda Pregunta")
        q2.save()

        q2_opt1=QuestionOption(question=q2,option="primera opcion")
        q2_opt2=QuestionOption(question=q2,option="segunda opcion")
        q2_opt1.save()
        q2_opt2.save()

        self.v2=Voting(name="Segunda Votacion",question=q2, slug="slug2")
        self.v2.save()
        super().setUp()

    def tearDown(self):
        super().tearDown()
        self.v=None
        self.v2=None

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

    # duplicate YES option
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

    # duplicate NO option
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
    def test_add_yes_no_question(self):
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
    def test_add_before_yes_no(self):
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
        q = Question.objects.get(desc='This contain an order question')
        qo = QuestionOrder(question = q, option = 'First order')
        qo.save()
        q.save()

        self.assertRaises(ValidationError)
        self.assertRaisesRegex(ValidationError,"Duplicated order, please checkout question order")
        self.assertEquals(len(q.order_options.all()), 1)
    
    def test_exists(self):
        v=Voting.objects.get(name="Votacion")
        self.assertEquals(v.question.options.all()[0].option,"opcion1")
        self.assertEquals(v.question.options.all()[1].option,"opcion2")
        self.assertEquals(len(v.question.options.all()),2)

    def test_exists_with_order(self):
        q1=Question(desc="Pregunta con opciones ordenadas")
        q1.save()

        ord1 = QuestionOrder(question=q1, option="primera", order_number=2)
        ord1.save()
        ord2 = QuestionOrder(question=q1, option="segunda", order_number=1)
        ord2.save()

        v1=Voting(name="Votacion Ordenada",question=q1)
        v1.save()

        query1=Voting.objects.get(name="Votacion Ordenada").question.order_options.filter(option="primera").get()
        query2=Voting.objects.get(name="Votacion Ordenada").question.order_options.filter(option="segunda").get()

        self.assertEquals(query1.order_number,2)
        self.assertEquals(query2.order_number,1)

    def test_add_option_to_question(self):
        v1=Voting.objects.get(name="Votacion")
        q1=v1.question

        self.assertEquals(len(q1.options.all()),2)

        opt3=QuestionOption(question=q1,option="opcion3")
        opt3.save()
        v1.save()

        self.assertEquals(Voting.objects.get(name="Votacion").question.options.all()[2].option,"opcion3")
        self.assertEquals(len(Voting.objects.get(name="Votacion").question.options.all()),3)

    def test_add_order_to_existing_question(self):
        v_bd=Voting.objects.get(name="Segunda Votacion")
        q_bd=v_bd.question

        for opt in q_bd.options.all():
            opt=opt.option
            Question.objects.get(desc="Segunda Pregunta").options.filter(option=opt).delete()

        options=Voting.objects.get(name="Segunda Votacion").question.options.all()
        self.assertFalse(options.count()!=0) #Comprueba que se han eliminado las opciones no ordenadas

        ord1 = QuestionOrder(question=q_bd, option="primera ordenada", order_number=2)
        ord1.save()
        ord2 = QuestionOrder(question=q_bd, option="segunda ordenada", order_number=1)
        ord2.save()

        v_bd.save()

        order_options=Voting.objects.get(name="Segunda Votacion").question.order_options.all()
        self.assertTrue(order_options.count()==2)

        query1=Voting.objects.get(name="Segunda Votacion").question.order_options.filter(option="primera ordenada").get()
        query2=Voting.objects.get(name="Segunda Votacion").question.order_options.filter(option="segunda ordenada").get()

        self.assertEquals(query1.order_number,2)
        self.assertEquals(query2.order_number,1)

    def test_invalid_order_number(self):
        q=Question(desc="Pregunta con orden invalido")
        q.save()
        order_number='error'
        QuestionOrder(question=q, option="error", order_number=order_number)

        self.assertRaises(ValueError)
        self.assertRaisesRegex(ValueError,"ValueError: invalid literal for int() with base 10: {}".format(order_number))

    def test_delete_when_unselect(self):
        q = Question.objects.get(desc='This is a test yes/no question')
        q.is_yes_no_question = False
        q.save()

        self.assertEquals(len(q.options.all()), 0)


class VotingViewsTestCase(StaticLiveServerTestCase):

    def setUp(self):
        # Load base test functionality for decide
        self.base = BaseTestCase()
        self.base.setUp()

        self.vars = {}

        options = webdriver.ChromeOptions()
        options.headless = True
        self.driver = webdriver.Chrome(options=options)

        super().setUp()

    def tearDown(self):
        super().tearDown()
        self.driver.quit()

        self.base.tearDown()

    def wait_for_window(self, timeout = 2):
        time.sleep(round(timeout / 1000))
        wh_now = self.driver.window_handles
        wh_then = self.vars["window_handles"]
        if len(wh_now) > len(wh_then):
            return set(wh_now).difference(set(wh_then)).pop()

    def test_duplicity_yes(self):

        # add the user and login
        User.objects.create_superuser('superuser', 'superuser@decide.com', 'superuser')
        self.driver.get(f'{self.live_server_url}/admin/')
        self.driver.find_element_by_id('id_username').send_keys("superuser")
        self.driver.find_element_by_id('id_password').send_keys("superuser", Keys.ENTER)

        driver = self.driver
        driver.find_element_by_xpath("//a[contains(@href, '/admin/voting/question/add/')]").click()
        driver.find_element_by_id("id_desc").click()
        driver.find_element_by_id("id_desc").clear()
        driver.find_element_by_id("id_desc").send_keys("Test duplicity with yes")
        driver.find_element_by_id("id_is_yes_no_question").click()
        driver.find_element_by_name("_save").click()
        driver.find_element_by_xpath("(//a[contains(text(),'Test duplicity with yes')])[2]").click()
        self.assertEqual("YES", driver.find_element_by_id("id_options-0-option").text)
        self.assertEqual("NO", driver.find_element_by_id("id_options-1-option").text)
        self.assertEqual("0", driver.find_element_by_id("id_options-0-number").get_attribute("value"))
        self.assertEqual("1", driver.find_element_by_id("id_options-1-number").get_attribute("value"))
        self.assertEqual("", driver.find_element_by_id("id_options-2-option").get_attribute("value"))
        driver.find_element_by_id("id_options-2-option").clear()
        driver.find_element_by_id("id_options-2-option").send_keys("YES")
        driver.find_element_by_xpath("//tr[@id='options-2']/td[4]").click()
        driver.find_element_by_name("_save").click()
        driver.find_element_by_xpath("(//a[contains(text(),'Test duplicity with yes')])[2]").click()
        self.assertEqual("0", driver.find_element_by_id("id_options-0-number").get_attribute("value"))
        self.assertEqual("YES", driver.find_element_by_id("id_options-0-option").text)
        self.assertEqual("1", driver.find_element_by_id("id_options-1-number").get_attribute("value"))
        self.assertEqual("NO", driver.find_element_by_id("id_options-1-option").text)
        self.assertEqual("", driver.find_element_by_id("id_options-2-option").get_attribute("value"))


    def test_delete_when_unselect(self):

        User.objects.create_superuser('superuser', 'superuser@decide.com', 'superuser')
        self.driver.get(f'{self.live_server_url}/admin/')
        self.driver.find_element_by_id('id_username').send_keys("superuser")
        self.driver.find_element_by_id('id_password').send_keys("superuser", Keys.ENTER)

        driver = self.driver
        driver.find_element_by_xpath("//a[contains(@href, '/admin/voting/question/add/')]").click()
        driver.find_element_by_id("id_desc").click()
        driver.find_element_by_id("id_desc").clear()
        driver.find_element_by_id("id_desc").send_keys("Delete when unselected")
        driver.find_element_by_xpath("//form[@id='question_form']/div/fieldset/div[2]/div/label").click()
        driver.find_element_by_name("_save").click()
        driver.find_element_by_xpath("(//a[contains(text(),'Delete when unselected')])[2]").click()
        driver.find_element_by_xpath("//form[@id='question_form']/div/fieldset/div[2]/div/label").click()
        self.assertEqual("YES", driver.find_element_by_id("id_options-0-option").text)
        self.assertEqual("NO", driver.find_element_by_id("id_options-1-option").text)
        self.assertEqual("0", driver.find_element_by_id("id_options-0-number").get_attribute("value"))
        self.assertEqual("1", driver.find_element_by_id("id_options-1-number").get_attribute("value"))
        driver.find_element_by_name("_save").click()
        driver.find_element_by_xpath("(//a[contains(text(),'Delete when unselected')])[2]").click()
        self.assertEqual("", driver.find_element_by_id("id_options-0-option").get_attribute("value"))


    def test_delete_previous_opt(self):

        User.objects.create_superuser('superuser', 'superuser@decide.com', 'superuser')
        self.driver.get(f'{self.live_server_url}/admin/')
        self.driver.find_element_by_id('id_username').send_keys("superuser")
        self.driver.find_element_by_id('id_password').send_keys("superuser", Keys.ENTER)
        
        driver = self.driver
        driver.find_element_by_xpath("//a[contains(@href, '/admin/voting/question/add/')]").click()
        driver.find_element_by_id("id_desc").clear()
        driver.find_element_by_id("id_desc").send_keys("Delete options")
        driver.find_element_by_id("id_options-0-option").click()
        driver.find_element_by_id("id_options-0-option").clear()
        driver.find_element_by_id("id_options-0-option").send_keys("First Option")
        driver.find_element_by_id("id_options-1-option").click()
        driver.find_element_by_id("id_options-1-option").clear()
        driver.find_element_by_id("id_options-1-option").send_keys("Second Option")
        driver.find_element_by_name("_save").click()
        driver.find_element_by_xpath("(//a[contains(text(),'Delete options')])[2]").click()
        driver.find_element_by_id("id_is_yes_no_question").click()
        driver.find_element_by_name("_save").click()
        driver.find_element_by_xpath("(//a[contains(text(),'Delete options')])[2]").click()
        self.assertEqual("YES", driver.find_element_by_id("id_options-0-option").text)
        self.assertEqual("NO", driver.find_element_by_id("id_options-1-option").text)
        self.assertNotRegexpMatches(driver.find_element_by_css_selector("BODY").text, r"^[\s\S]*id=id_options-2-option[\s\S]*$")
        self.assertNotRegexpMatches(driver.find_element_by_css_selector("BODY").text, r"^[\s\S]*id=id_options-3-option[\s\S]*$")
        self.assertNotRegexpMatches(driver.find_element_by_css_selector("BODY").text, r"^[\s\S]*id=id_options-4-option[\s\S]*$")


    def test_duplicity_no(self):

        User.objects.create_superuser('superuser', 'superuser@decide.com', 'superuser')
        self.driver.get(f'{self.live_server_url}/admin/')
        self.driver.find_element_by_id('id_username').send_keys("superuser")
        self.driver.find_element_by_id('id_password').send_keys("superuser", Keys.ENTER)

        driver = self.driver
        driver.find_element_by_xpath("//a[contains(@href, '/admin/voting/question/add/')]").click()
        driver.find_element_by_id("id_desc").click()
        driver.find_element_by_id("id_desc").clear()
        driver.find_element_by_id("id_desc").send_keys("Test duplicity with yes")
        driver.find_element_by_id("id_is_yes_no_question").click()
        driver.find_element_by_name("_save").click()
        driver.find_element_by_xpath("(//a[contains(text(),'Test duplicity with yes')])[2]").click()
        self.assertEqual("YES", driver.find_element_by_id("id_options-0-option").text)
        self.assertEqual("NO", driver.find_element_by_id("id_options-1-option").text)
        self.assertEqual("0", driver.find_element_by_id("id_options-0-number").get_attribute("value"))
        self.assertEqual("1", driver.find_element_by_id("id_options-1-number").get_attribute("value"))
        self.assertEqual("", driver.find_element_by_id("id_options-2-option").get_attribute("value"))
        driver.find_element_by_id("id_options-2-option").clear()
        driver.find_element_by_id("id_options-2-option").send_keys("NO")
        driver.find_element_by_xpath("//tr[@id='options-2']/td[4]").click()
        driver.find_element_by_name("_save").click()
        driver.find_element_by_xpath("(//a[contains(text(),'Test duplicity with yes')])[2]").click()
        self.assertEqual("0", driver.find_element_by_id("id_options-0-number").get_attribute("value"))
        self.assertEqual("YES", driver.find_element_by_id("id_options-0-option").text)
        self.assertEqual("1", driver.find_element_by_id("id_options-1-number").get_attribute("value"))
        self.assertEqual("NO", driver.find_element_by_id("id_options-1-option").text)
        self.assertEqual("", driver.find_element_by_id("id_options-2-option").get_attribute("value"))


    def test_duplicity_yes_and_no(self):

        User.objects.create_superuser('superuser', 'superuser@decide.com', 'superuser')
        self.driver.get(f'{self.live_server_url}/admin/')
        self.driver.find_element_by_id('id_username').send_keys("superuser")
        self.driver.find_element_by_id('id_password').send_keys("superuser", Keys.ENTER)

        driver = self.driver
        driver.find_element_by_xpath("//a[contains(@href, '/admin/voting/question/add/')]").click()
        driver.find_element_by_id("id_desc").clear()
        driver.find_element_by_id("id_desc").send_keys("Duplicity")
        driver.find_element_by_xpath("//form[@id='question_form']/div/fieldset/div[2]/div/label").click()
        driver.find_element_by_name("_save").click()
        driver.find_element_by_xpath("(//a[contains(text(),'Duplicity')])[2]").click()
        driver.find_element_by_name("_save").click()
        driver.find_element_by_xpath("(//a[contains(text(),'Duplicity')])[2]").click()
        self.assertEqual("0", driver.find_element_by_id("id_options-0-number").get_attribute("value"))
        self.assertEqual("YES", driver.find_element_by_id("id_options-0-option").text)
        self.assertEqual("1", driver.find_element_by_id("id_options-1-number").get_attribute("value"))
        self.assertEqual("NO", driver.find_element_by_id("id_options-1-option").text)
        self.assertEqual("", driver.find_element_by_id("id_options-2-option").get_attribute("value"))

    def test_create_voting_blank_url(self):
        User.objects.create_superuser('superuser', 'superuser@decide.com', 'superuser')
        #Proceso para loguearse como administrador
        self.driver.get(f'{self.live_server_url}/admin/')
        self.driver.find_element_by_id('id_username').send_keys("superuser")
        self.driver.find_element_by_id('id_password').send_keys("superuser", Keys.ENTER)
        #Entramos al formulario para crear una votación
        time.sleep(1)
        # xpath=//a[contains(@href, '/admin/voting/voting/add/')]
        self.driver.find_element(By.CSS_SELECTOR, ".model-voting .addlink").click()
        time.sleep(1)
        self.driver.find_element_by_id('id_name').send_keys("Voting selenium test")
        self.driver.find_element_by_id('id_desc').send_keys("Voting selenium test desc")
        self.driver.find_element_by_id('id_question').click()
        self.vars["window_handles"] = self.driver.window_handles
        #Proceso para añadir una pregunta y sus opciones
        self.driver.find_element(By.CSS_SELECTOR, "#add_id_question > img").click()
        self.vars["win2433"] = self.wait_for_window(2000)
        self.vars["root"] = self.driver.current_window_handle
        self.driver.switch_to.window(self.vars["win2433"])
        self.driver.find_element(By.ID, "id_desc").click()
        self.driver.find_element(By.ID, "id_desc").send_keys("Question description")
        self.driver.find_element(By.ID, "id_options-0-option").click()
        self.driver.find_element(By.ID, "id_options-0-option").send_keys("Option 1")
        self.driver.find_element(By.ID, "id_options-1-option").click()
        self.driver.find_element(By.ID, "id_options-1-option").send_keys("Option 2")
        self.driver.find_element(By.NAME, "_save").click()
        self.driver.switch_to.window(self.vars["root"])
        #Vuelta a la vista para crear una votación, y creación de un Auth
        self.vars["window_handles"] = self.driver.window_handles
        self.driver.find_element(By.CSS_SELECTOR, "#add_id_auths > img").click()
        self.vars["win1901"] = self.wait_for_window(2000)
        self.driver.switch_to.window(self.vars["win1901"])
        self.driver.find_element(By.ID, "id_name").send_keys("auth")
        self.driver.find_element(By.ID, "id_url").click()
        self.driver.find_element(By.ID, "id_url").send_keys(f'{self.live_server_url}')
        self.driver.find_element(By.NAME, "_save").click()
        #Proceso para guardar la votación, y comprobar el error resultante
        self.driver.switch_to.window(self.vars["root"])
        self.driver.find_element(By.NAME, "_save").click()
        self.assertEqual("Please correct the error below.", self.driver.find_element_by_xpath("//form[@id='voting_form']/div/p").text)
        self.assertEqual("This field is required.", self.driver.find_element_by_xpath("//form[@id='voting_form']/div/fieldset/div[4]/ul/li").text)

    def test_create_voting_wrong_url(self):
        User.objects.create_superuser('superuser', 'superuser@decide.com', 'superuser')
        #Proceso para loguearse como administrador
        self.driver.get(f'{self.live_server_url}/admin/')
        self.driver.find_element_by_id('id_username').send_keys("superuser")
        self.driver.find_element_by_id('id_password').send_keys("superuser", Keys.ENTER)
        #Entramos al formulario para crear una votación
        time.sleep(1)
        # xpath=//a[contains(@href, '/admin/voting/voting/add/')]
        self.driver.find_element(By.CSS_SELECTOR, ".model-voting .addlink").click()
        time.sleep(1)
        self.driver.find_element_by_id('id_name').send_keys("Voting selenium test")
        self.driver.find_element_by_id('id_desc').send_keys("Voting selenium test desc")
        self.driver.find_element_by_id('id_slug').send_keys("¡!")
        self.driver.find_element_by_id('id_question').click()
        self.vars["window_handles"] = self.driver.window_handles
        #Proceso para añadir una pregunta y sus opciones
        self.driver.find_element(By.CSS_SELECTOR, "#add_id_question > img").click()
        self.vars["win2433"] = self.wait_for_window(2000)
        self.vars["root"] = self.driver.current_window_handle
        self.driver.switch_to.window(self.vars["win2433"])
        self.driver.find_element(By.ID, "id_desc").click()
        self.driver.find_element(By.ID, "id_desc").send_keys("Question description")
        self.driver.find_element(By.ID, "id_options-0-option").click()
        self.driver.find_element(By.ID, "id_options-0-option").send_keys("Option 1")
        self.driver.find_element(By.ID, "id_options-1-option").click()
        self.driver.find_element(By.ID, "id_options-1-option").send_keys("Option 2")
        self.driver.find_element(By.NAME, "_save").click()
        self.driver.switch_to.window(self.vars["root"])
        #Vuelta a la vista para crear una votación, y creación de un Auth
        self.vars["window_handles"] = self.driver.window_handles
        self.driver.find_element(By.CSS_SELECTOR, "#add_id_auths > img").click()
        self.vars["win1901"] = self.wait_for_window(2000)
        self.driver.switch_to.window(self.vars["win1901"])
        self.driver.find_element(By.ID, "id_name").send_keys("auth")
        self.driver.find_element(By.ID, "id_url").click()
        self.driver.find_element(By.ID, "id_url").send_keys(f'{self.live_server_url}')
        self.driver.find_element(By.NAME, "_save").click()
        #Proceso para guardar la votación, y comprobar el error resultante
        self.driver.switch_to.window(self.vars["root"])
        self.driver.find_element(By.NAME, "_save").click()
        self.assertEqual("Please correct the error below.", self.driver.find_element_by_xpath("//form[@id='voting_form']/div/p").text)
        self.assertEqual("Only letters and numbers are allowed.", self.driver.find_element_by_xpath("//form[@id='voting_form']/div/fieldset/div[4]/ul/li").text)


    def test_delete_yes_with_yes_no_selected(self):

        User.objects.create_superuser('superuser', 'superuser@decide.com', 'superuser')
        self.driver.get(f'{self.live_server_url}/admin/')
        self.driver.find_element_by_id('id_username').send_keys("superuser")
        self.driver.find_element_by_id('id_password').send_keys("superuser", Keys.ENTER)

        driver = self.driver
        driver.find_element_by_xpath("//a[contains(@href, '/admin/voting/question/add/')]").click()
        driver.find_element_by_id("id_desc").click()
        driver.find_element_by_id("id_desc").clear()
        driver.find_element_by_id("id_desc").send_keys("Test delete yes with YES/NO selected")
        driver.find_element_by_id("id_is_yes_no_question").click()
        driver.find_element_by_name("_save").click()
        driver.find_element_by_xpath("(//a[contains(text(),'Test delete yes with YES/NO selected')])[2]").click()
        self.assertEqual("0", driver.find_element_by_id("id_options-0-number").get_attribute("value"))
        self.assertEqual("YES", driver.find_element_by_id("id_options-0-option").text)
        self.assertEqual("1", driver.find_element_by_id("id_options-1-number").get_attribute("value"))
        self.assertEqual("NO", driver.find_element_by_id("id_options-1-option").text)
        self.assertEqual("", driver.find_element_by_id("id_options-2-option").get_attribute("value"))
        driver.find_element_by_id("id_options-0-DELETE").click()
        driver.find_element_by_name("_save").click()
        driver.find_element_by_xpath("(//a[contains(text(),'Test delete yes with YES/NO selected')])[2]").click()
        self.assertEqual("0", driver.find_element_by_id("id_options-0-number").get_attribute("value"))
        self.assertEqual("YES", driver.find_element_by_id("id_options-0-option").text)
        self.assertEqual("1", driver.find_element_by_id("id_options-1-number").get_attribute("value"))
        self.assertEqual("NO", driver.find_element_by_id("id_options-1-option").text)
        self.assertEqual("", driver.find_element_by_id("id_options-2-option").get_attribute("value"))


    def test_delete_no_with_yes_no_selected(self):

        User.objects.create_superuser('superuser', 'superuser@decide.com', 'superuser')
        self.driver.get(f'{self.live_server_url}/admin/')
        self.driver.find_element_by_id('id_username').send_keys("superuser")
        self.driver.find_element_by_id('id_password').send_keys("superuser", Keys.ENTER)

        driver = self.driver
        driver.find_element_by_xpath("//a[contains(@href, '/admin/voting/question/add/')]").click()
        driver.find_element_by_id("id_desc").click()
        driver.find_element_by_id("id_desc").clear()
        driver.find_element_by_id("id_desc").send_keys("Test delete no with YES/NO selected")
        driver.find_element_by_id("id_is_yes_no_question").click()
        driver.find_element_by_name("_save").click()
        driver.find_element_by_xpath("(//a[contains(text(),'Test delete no with YES/NO selected')])[2]").click()
        self.assertEqual("0", driver.find_element_by_id("id_options-0-number").get_attribute("value"))
        self.assertEqual("YES", driver.find_element_by_id("id_options-0-option").text)
        self.assertEqual("1", driver.find_element_by_id("id_options-1-number").get_attribute("value"))
        self.assertEqual("NO", driver.find_element_by_id("id_options-1-option").text)
        self.assertEqual("", driver.find_element_by_id("id_options-2-option").get_attribute("value"))
        driver.find_element_by_id("id_options-1-DELETE").click()
        driver.find_element_by_name("_save").click()
        driver.find_element_by_xpath("(//a[contains(text(),'Test delete no with YES/NO selected')])[2]").click()
        self.assertEqual("0", driver.find_element_by_id("id_options-0-number").get_attribute("value"))
        self.assertEqual("YES", driver.find_element_by_id("id_options-0-option").text)
        self.assertEqual("1", driver.find_element_by_id("id_options-1-number").get_attribute("value"))
        self.assertEqual("NO", driver.find_element_by_id("id_options-1-option").text)
        self.assertEqual("", driver.find_element_by_id("id_options-2-option").get_attribute("value"))

    def test_add_before_yes_no(self):

        User.objects.create_superuser('superuser', 'superuser@decide.com', 'superuser')
        self.driver.get(f'{self.live_server_url}/admin/')
        self.driver.find_element_by_id('id_username').send_keys("superuser")
        self.driver.find_element_by_id('id_password').send_keys("superuser", Keys.ENTER)

        driver = self.driver
        driver.find_element_by_xpath("//a[contains(@href, '/admin/voting/question/add/')]").click()
        driver.find_element_by_id("id_desc").clear()
        driver.find_element_by_id("id_desc").send_keys("Test add before YES/NO question")
        driver.find_element_by_id("id_is_yes_no_question").click()
        driver.find_element_by_name("_save").click()
        driver.find_element_by_xpath("(//a[contains(text(),'Test add before YES/NO question')])[2]").click()
        self.assertEqual("0", driver.find_element_by_id("id_options-0-number").get_attribute("value"))
        self.assertEqual("YES", driver.find_element_by_id("id_options-0-option").text)
        self.assertEqual("1", driver.find_element_by_id("id_options-1-number").get_attribute("value"))
        self.assertEqual("NO", driver.find_element_by_id("id_options-1-option").text)
        self.assertEqual("", driver.find_element_by_id("id_options-2-option").get_attribute("value"))
        driver.find_element_by_id("id_options-2-option").clear()
        driver.find_element_by_id("id_options-2-option").send_keys("Something")
        driver.find_element_by_name("_save").click()
        driver.find_element_by_xpath("(//a[contains(text(),'Test add before YES/NO question')])[2]").click()
        self.assertEqual("0", driver.find_element_by_id("id_options-0-number").get_attribute("value"))
        self.assertEqual("YES", driver.find_element_by_id("id_options-0-option").text)
        self.assertEqual("1", driver.find_element_by_id("id_options-1-number").get_attribute("value"))
        self.assertEqual("NO", driver.find_element_by_id("id_options-1-option").text)
        self.assertEqual("", driver.find_element_by_id("id_options-2-option").get_attribute("value"))


    def test_add_yes_no_question(self):

        User.objects.create_superuser('superuser', 'superuser@decide.com', 'superuser')
        self.driver.get(f'{self.live_server_url}/admin/')
        self.driver.find_element_by_id('id_username').send_keys("superuser")
        self.driver.find_element_by_id('id_password').send_keys("superuser", Keys.ENTER)

        driver = self.driver
        driver.find_element_by_xpath("//a[contains(@href, '/admin/voting/question/add/')]").click()
        driver.find_element_by_id("id_desc").clear()
        driver.find_element_by_id("id_desc").send_keys("Test add YES/NO question")
        driver.find_element_by_id("id_is_yes_no_question").click()
        driver.find_element_by_name("_save").click()
        driver.find_element_by_xpath("(//a[contains(text(),'Test add YES/NO question')])[2]").click()
        self.assertEqual("0", driver.find_element_by_id("id_options-0-number").get_attribute("value"))
        self.assertEqual("YES", driver.find_element_by_id("id_options-0-option").text)
        self.assertEqual("1", driver.find_element_by_id("id_options-1-number").get_attribute("value"))
        self.assertEqual("NO", driver.find_element_by_id("id_options-1-option").text)
        self.assertEqual("", driver.find_element_by_id("id_options-2-option").get_attribute("value"))


    def test_duplicity_order(self):

        User.objects.create_superuser('superuser', 'superuser@decide.com', 'superuser')
        self.driver.get(f'{self.live_server_url}/admin/')
        self.driver.find_element_by_id('id_username').send_keys("superuser")
        self.driver.find_element_by_id('id_password').send_keys("superuser", Keys.ENTER)

        driver = self.driver
        driver.find_element_by_xpath("//a[contains(@href, '/admin/voting/question/add/')]").click()
        driver.find_element_by_id("id_desc").clear()
        driver.find_element_by_id("id_desc").send_keys("Test duplicity order name")
        driver.find_element_by_id("id_order_options-0-option").click()
        driver.find_element_by_xpath("//tr[@id='order_options-0']/td[4]").click()
        driver.find_element_by_id("id_order_options-0-option").clear()
        driver.find_element_by_id("id_order_options-0-option").send_keys("Hi Pepito")
        driver.find_element_by_id("id_order_options-1-option").click()
        driver.find_element_by_id("id_order_options-1-option").clear()
        driver.find_element_by_id("id_order_options-1-option").send_keys("Hi Pepito")
        driver.find_element_by_name("_save").click()
        driver.find_element_by_xpath("(//a[contains(text(),'Test duplicity order name')])[2]").click()
        self.assertEqual("Hi Pepito", driver.find_element_by_id("id_order_options-0-option").text)
        self.assertEqual("", driver.find_element_by_id("id_order_options-1-option").get_attribute("value"))


    def test_duplicity_option(self):

        User.objects.create_superuser('superuser', 'superuser@decide.com', 'superuser')
        self.driver.get(f'{self.live_server_url}/admin/')
        self.driver.find_element_by_id('id_username').send_keys("superuser")
        self.driver.find_element_by_id('id_password').send_keys("superuser", Keys.ENTER)

        driver = self.driver
        driver.find_element_by_xpath("//a[contains(@href, '/admin/voting/question/add/')]").click()
        driver.find_element_by_id("id_desc").clear()
        driver.find_element_by_id("id_desc").send_keys("Duplicity Option")
        driver.find_element_by_id("id_options-0-option").click()
        driver.find_element_by_id("id_options-0-option").clear()
        driver.find_element_by_id("id_options-0-option").send_keys("First Option")
        driver.find_element_by_id("id_options-1-option").click()
        driver.find_element_by_id("id_options-1-option").clear()
        driver.find_element_by_id("id_options-1-option").send_keys("Second Option")
        driver.find_element_by_name("_save").click()
        driver.find_element_by_xpath("(//a[contains(text(),'Duplicity Option')])[2]").click()
        driver.find_element_by_id("id_options-2-option").click()
        driver.find_element_by_id("id_options-2-option").clear()
        driver.find_element_by_id("id_options-2-option").send_keys("First Option")
        driver.find_element_by_name("_save").click()
        driver.find_element_by_xpath("(//a[contains(text(),'Duplicity Option')])[2]").click()
        self.assertEqual("2", driver.find_element_by_id("id_options-0-number").get_attribute("value"))
        self.assertEqual("First Option", driver.find_element_by_id("id_options-0-option").text)
        self.assertEqual("3", driver.find_element_by_id("id_options-1-number").get_attribute("value"))
        self.assertEqual("Second Option", driver.find_element_by_id("id_options-1-option").text)
        self.assertEqual("", driver.find_element_by_id("id_options-2-number").get_attribute("value"))
        self.assertEqual("", driver.find_element_by_id("id_options-2-option").text)

    def test_view_create_voting(self):
        User.objects.create_superuser('superuser', 'superuser@decide.com', 'superuser')
        #Proceso para loguearse como administrador
        self.driver.get(f'{self.live_server_url}/admin/')
        self.driver.find_element_by_id('id_username').send_keys("superuser")
        self.driver.find_element_by_id('id_password').send_keys("superuser", Keys.ENTER)
        #Proceso para añadir una pregunta y sus opciones
        self.assertTrue(len(self.driver.find_elements_by_id('user-tools')) == 1)
        time.sleep(1)
        self.driver.find_element(By.LINK_TEXT, "Votings").click()
        time.sleep(1)
        assert self.driver.find_element(By.CSS_SELECTOR, "#content > h1").text == "Select voting to change"
        self.driver.find_element(By.CSS_SELECTOR, ".addlink").click()
        self.driver.find_element_by_id('id_name').send_keys("Voting selenium test")
        self.driver.find_element_by_id('id_desc').send_keys("Voting selenium test desc")
        self.driver.find_element_by_id('id_slug').send_keys("seleniumtest")
        self.driver.find_element_by_id('id_question').click()
        self.vars["window_handles"] = self.driver.window_handles
        #Proceso para añadir una pregunta y sus opciones
        self.driver.find_element(By.CSS_SELECTOR, "#add_id_question > img").click()
        self.vars["win2433"] = self.wait_for_window(2000)
        self.vars["root"] = self.driver.current_window_handle
        self.driver.switch_to.window(self.vars["win2433"])
        self.driver.find_element(By.ID, "id_desc").click()
        self.driver.find_element(By.ID, "id_desc").send_keys("Question description")
        self.driver.find_element(By.ID, "id_options-0-option").click()
        self.driver.find_element(By.ID, "id_options-0-option").send_keys("Option 1")
        self.driver.find_element(By.ID, "id_options-1-option").click()
        self.driver.find_element(By.ID, "id_options-1-option").send_keys("Option 2")
        self.driver.find_element(By.NAME, "_save").click()
        self.driver.switch_to.window(self.vars["root"])
        #Vuelta a la vista para crear una votación, y creación de un Auth
        self.vars["window_handles"] = self.driver.window_handles
        self.driver.find_element(By.CSS_SELECTOR, "#add_id_auths > img").click()
        self.vars["win1901"] = self.wait_for_window(2000)
        self.driver.switch_to.window(self.vars["win1901"])
        self.driver.find_element(By.ID, "id_name").send_keys("auth")
        self.driver.find_element(By.ID, "id_url").click()
        self.driver.find_element(By.ID, "id_url").send_keys(f'{self.live_server_url}')
        self.driver.find_element(By.NAME, "_save").click()
        #Proceso para guardar la votación, y comprobar si se ha realizado correctamente
        self.driver.switch_to.window(self.vars["root"])
        self.driver.find_element(By.NAME, "_save").click()
        self.driver.find_element(By.CSS_SELECTOR, ".row1 a").click()
        assert self.driver.find_element(By.CSS_SELECTOR, "#content > h1").text == "Change voting"

    def test_view_create_ordering_voting(self):
        User.objects.create_superuser('superuser', 'superuser@decide.com', 'superuser')
        #Proceso para loguearse como administrador
        self.driver.get(f'{self.live_server_url}/admin/')
        self.driver.find_element_by_id('id_username').send_keys("superuser")
        self.driver.find_element_by_id('id_password').send_keys("superuser", Keys.ENTER)
        #Proceso para crear una votación
        self.assertTrue(len(self.driver.find_elements_by_id('user-tools')) == 1)
        time.sleep(1)
        self.driver.find_element(By.LINK_TEXT, "Votings").click()
        time.sleep(1)
        assert self.driver.find_element(By.CSS_SELECTOR, "#content > h1").text == "Select voting to change"
        self.driver.find_element(By.CSS_SELECTOR, ".addlink").click()
        self.driver.find_element_by_id('id_name').send_keys("Ordering voting test")
        self.driver.find_element_by_id('id_desc').send_keys("Ordering voting test desc")
        self.driver.find_element_by_id('id_slug').send_keys("seleniumtest")
        self.driver.find_element_by_id('id_question').click()
        self.vars["window_handles"] = self.driver.window_handles
        #Proceso para añadir una pregunta y sus opciones
        self.driver.find_element(By.CSS_SELECTOR, "#add_id_question > img").click()
        self.vars["win8328"] = self.wait_for_window(2000)
        self.vars["root"] = self.driver.current_window_handle
        self.driver.switch_to.window(self.vars["win8328"])
        self.driver.find_element(By.ID, "id_desc").send_keys("Voting ordering question description")
        self.driver.find_element(By.CSS_SELECTOR, "#options-group h2").click()
        self.driver.find_element(By.ID, "id_order_options-0-order_number").send_keys("1")
        self.driver.find_element(By.ID, "id_order_options-0-order_number").click()
        self.driver.find_element(By.ID, "id_order_options-1-order_number").send_keys("2")
        self.driver.find_element(By.ID, "id_order_options-1-order_number").click()
        element = self.driver.find_element(By.ID, "id_order_options-1-order_number")
        actions = ActionChains(self.driver)
        actions.double_click(element).perform()
        self.driver.find_element(By.ID, "id_order_options-0-option").click()
        self.driver.find_element(By.ID, "id_order_options-0-option").send_keys("Question option one")
        self.driver.find_element(By.ID, "id_order_options-1-option").click()
        self.driver.find_element(By.ID, "id_order_options-1-option").send_keys("Question option two")
        self.driver.find_element(By.CSS_SELECTOR, "#order_options-0 > .field-number").click()
        self.driver.find_element(By.NAME, "_save").click()
        #Vuelta a la vista para crear una votación, y creación de un Auth
        self.vars["window_handles"] = self.driver.window_handles
        self.driver.switch_to.window(self.vars["root"])
        self.driver.find_element(By.CSS_SELECTOR, "#add_id_auths > img").click()
        self.vars["win6682"] = self.wait_for_window(2000)
        self.driver.switch_to.window(self.vars["win6682"])
        self.driver.find_element(By.ID, "id_name").send_keys("localhost")
        self.driver.find_element(By.ID, "id_url").send_keys(f'{self.live_server_url}')
        self.driver.find_element(By.NAME, "_save").click()
        #Proceso para guardar la votación, y comprobar si se ha realizado correctamente
        self.driver.switch_to.window(self.vars["root"])
        self.driver.find_element(By.NAME, "_save").click()
        self.driver.find_element(By.CSS_SELECTOR, ".row1 a").click()
        assert self.driver.find_element(By.CSS_SELECTOR, "#content > h1").text == "Change voting"

    def test_view_update_voting(self):
        User.objects.create_superuser('superuser', 'superuser@decide.com', 'superuser')
        #Proceso para loguearse como administrador
        self.driver.get(f'{self.live_server_url}/admin/')
        self.driver.find_element_by_id('id_username').send_keys("superuser")
        self.driver.find_element_by_id('id_password').send_keys("superuser", Keys.ENTER)
        #Proceso para crear una votación
        self.assertTrue(len(self.driver.find_elements_by_id('user-tools')) == 1)
        time.sleep(1)
        self.driver.find_element(By.LINK_TEXT, "Votings").click()
        time.sleep(1)
        assert self.driver.find_element(By.CSS_SELECTOR, "#content > h1").text == "Select voting to change"
        self.driver.find_element(By.CSS_SELECTOR, ".addlink").click()
        self.driver.find_element_by_id('id_name').send_keys("Ordering voting test")
        self.driver.find_element_by_id('id_desc').send_keys("Ordering voting test desc")
        self.driver.find_element_by_id('id_slug').send_keys("seleniumtest")
        self.driver.find_element_by_id('id_question').click()
        self.vars["window_handles"] = self.driver.window_handles
        #Proceso para añadir una pregunta y sus opciones
        self.driver.find_element(By.CSS_SELECTOR, "#add_id_question > img").click()
        self.vars["win8328"] = self.wait_for_window(2000)
        self.vars["root"] = self.driver.current_window_handle
        self.driver.switch_to.window(self.vars["win8328"])
        self.driver.find_element(By.ID, "id_desc").send_keys("Voting ordering question description")
        self.driver.find_element(By.CSS_SELECTOR, "#options-group h2").click()
        self.driver.find_element(By.ID, "id_order_options-0-order_number").send_keys("1")
        self.driver.find_element(By.ID, "id_order_options-0-order_number").click()
        self.driver.find_element(By.ID, "id_order_options-1-order_number").send_keys("2")
        self.driver.find_element(By.ID, "id_order_options-1-order_number").click()
        element = self.driver.find_element(By.ID, "id_order_options-1-order_number")
        actions = ActionChains(self.driver)
        actions.double_click(element).perform()
        self.driver.find_element(By.ID, "id_order_options-0-option").click()
        self.driver.find_element(By.ID, "id_order_options-0-option").send_keys("Question option one")
        self.driver.find_element(By.ID, "id_order_options-1-option").click()
        self.driver.find_element(By.ID, "id_order_options-1-option").send_keys("Question option two")
        self.driver.find_element(By.CSS_SELECTOR, "#order_options-0 > .field-number").click()
        self.driver.find_element(By.NAME, "_save").click()
        #Vuelta a la vista para crear una votación, y creación de un Auth
        self.vars["window_handles"] = self.driver.window_handles
        self.driver.switch_to.window(self.vars["root"])
        self.driver.find_element(By.CSS_SELECTOR, "#add_id_auths > img").click()
        self.vars["win6682"] = self.wait_for_window(2000)
        self.driver.switch_to.window(self.vars["win6682"])
        self.driver.find_element(By.ID, "id_name").send_keys("localhost")
        self.driver.find_element(By.ID, "id_url").send_keys(f'{self.live_server_url}')
        self.driver.find_element(By.NAME, "_save").click()
        #Proceso para guardar la votación, y comprobar si se ha realizado correctamente
        self.driver.switch_to.window(self.vars["root"])
        self.driver.find_element(By.NAME, "_save").click()

        self.driver.find_element(By.NAME, "_selected_action").click()
        self.driver.find_element(By.NAME, "action").click()
        dropdown = self.driver.find_element(By.NAME, "action")
        dropdown.find_element(By.XPATH, "//option[. = 'Start']").click()
        self.driver.find_element(By.CSS_SELECTOR, "option:nth-child(3)").click()
        self.driver.find_element(By.NAME, "index").click()
        self.driver.find_element(By.NAME, "_selected_action").click()
        self.driver.find_element(By.NAME, "action").click()
        dropdown = self.driver.find_element(By.NAME, "action")
        dropdown.find_element(By.XPATH, "//option[. = 'Stop']").click()
        self.driver.find_element(By.CSS_SELECTOR, "option:nth-child(4)").click()
        self.driver.find_element(By.NAME, "index").click()
        self.driver.find_element(By.NAME, "_selected_action").click()
        self.driver.find_element(By.NAME, "action").click()
        dropdown = self.driver.find_element(By.NAME, "action")
        dropdown.find_element(By.XPATH, "//option[. = 'Tally']").click()
        self.driver.find_element(By.CSS_SELECTOR, "option:nth-child(5)").click()
        self.driver.find_element(By.NAME, "index").click()

    def test_negative_order_number(self):
        User.objects.create_superuser('superuser', 'superuser@decide.com', 'superuser')
        #Proceso para loguearse como administrador
        self.driver.get(f'{self.live_server_url}/admin/')
        self.driver.find_element_by_id('id_username').send_keys("superuser")
        self.driver.find_element_by_id('id_password').send_keys("superuser", Keys.ENTER)
        #Proceso para crear una votación
        self.assertTrue(len(self.driver.find_elements_by_id('user-tools')) == 1)
        time.sleep(1)
        self.driver.find_element(By.LINK_TEXT, "Votings").click()
        time.sleep(1)
        assert self.driver.find_element(By.CSS_SELECTOR, "#content > h1").text == "Select voting to change"
        self.driver.find_element(By.CSS_SELECTOR, ".addlink").click()
        self.driver.find_element_by_id('id_name').send_keys("Ordering voting test")
        self.driver.find_element_by_id('id_desc').send_keys("Ordering voting test desc")
        self.driver.find_element_by_id('id_slug').send_keys("seleniumtest")
        self.driver.find_element_by_id('id_question').click()
        self.vars["window_handles"] = self.driver.window_handles
        #Proceso para añadir una pregunta y sus opciones
        self.driver.find_element(By.CSS_SELECTOR, "#add_id_question > img").click()
        self.vars["win8328"] = self.wait_for_window(2000)
        self.vars["root"] = self.driver.current_window_handle
        self.driver.switch_to.window(self.vars["win8328"])
        self.driver.find_element_by_id("id_desc").click()
        self.driver.find_element_by_id("id_desc").clear()
        self.driver.find_element_by_id("id_desc").send_keys("Descripcion de la pregunta")
        self.driver.find_element_by_id("id_order_options-0-option").click()
        self.driver.find_element_by_id("id_order_options-0-option").clear()
        self.driver.find_element_by_id("id_order_options-0-option").send_keys("Primera opcion")
        self.driver.find_element_by_id("id_order_options-0-order_number").click()
        self.driver.find_element_by_id("id_order_options-0-order_number").clear()
        self.driver.find_element_by_id("id_order_options-0-order_number").send_keys("1")
        self.driver.find_element_by_id("id_order_options-1-option").click()
        self.driver.find_element_by_id("id_order_options-1-option").clear()
        self.driver.find_element_by_id("id_order_options-1-option").send_keys("Opcion negativa")
        self.driver.find_element_by_id("id_order_options-1-order_number").click()
        self.driver.find_element_by_id("id_order_options-1-order_number").clear()
        self.driver.find_element_by_id("id_order_options-1-order_number").send_keys("-1")
        self.driver.find_element_by_xpath("//tr[@id='order_options-1']/td[2]").click()
        self.driver.find_element_by_name("_save").click()
        self.assertEqual("Please correct the error below.", self.driver.find_element_by_xpath("//form[@id='question_form']/div/p").text)
        self.assertEqual("Ensure this value is greater than or equal to 0.", self.driver.find_element_by_xpath("//tr[@id='order_options-1']/td[2]/ul/li").text)
    
    def test_add_order_number_to_question(self):
        User.objects.create_superuser('superuser', 'superuser@decide.com', 'superuser')
        #Proceso para loguearse como administrador
        self.driver.get(f'{self.live_server_url}/admin/')
        self.driver.find_element_by_id('id_username').send_keys("superuser")
        self.driver.find_element_by_id('id_password').send_keys("superuser", Keys.ENTER)
        #Proceso para crear una votación
        self.assertTrue(len(self.driver.find_elements_by_id('user-tools')) == 1)
        time.sleep(1)
        self.driver.find_element(By.LINK_TEXT, "Votings").click()
        time.sleep(1)
        assert self.driver.find_element(By.CSS_SELECTOR, "#content > h1").text == "Select voting to change"
        self.driver.find_element(By.CSS_SELECTOR, ".addlink").click()
        self.driver.find_element_by_id('id_name').send_keys("Ordering voting test")
        self.driver.find_element_by_id('id_desc').send_keys("Ordering voting test desc")
        self.driver.find_element_by_id('id_slug').send_keys("seleniumtest")
        self.driver.find_element_by_id('id_question').click()
        self.vars["window_handles"] = self.driver.window_handles
        #Proceso para añadir una pregunta y sus opciones
        self.driver.find_element(By.CSS_SELECTOR, "#add_id_question > img").click()
        self.vars["win8328"] = self.wait_for_window(2000)
        self.vars["root"] = self.driver.current_window_handle
        self.driver.switch_to.window(self.vars["win8328"])
        self.driver.find_element_by_id("id_desc").click()
        self.driver.find_element_by_id("id_desc").clear()
        self.driver.find_element_by_id("id_desc").send_keys("Descripcion de la pregunta")
        self.driver.find_element_by_id("id_order_options-0-option").click()
        self.driver.find_element_by_id("id_order_options-0-option").clear()
        self.driver.find_element_by_id("id_order_options-0-option").send_keys("Primera opcion")
        self.driver.find_element_by_id("id_order_options-0-order_number").click()
        self.driver.find_element_by_id("id_order_options-0-order_number").clear()
        self.driver.find_element_by_id("id_order_options-0-order_number").send_keys("1")
        self.driver.find_element_by_id("id_order_options-1-option").click()
        self.driver.find_element_by_id("id_order_options-1-option").clear()
        self.driver.find_element_by_id("id_order_options-1-option").send_keys("Segunda opcion")
        self.driver.find_element_by_id("id_order_options-1-order_number").click()
        self.driver.find_element_by_id("id_order_options-1-order_number").clear()
        self.driver.find_element_by_id("id_order_options-1-order_number").send_keys("2")
        self.driver.find_element_by_name("_save").click()
        self.vars["window_handles"] = self.driver.window_handles
        self.driver.switch_to.window(self.vars["root"])
        self.driver.find_element_by_xpath("//img[@alt='Change']").click()
        self.vars["win8328"] = self.wait_for_window(2000)
        self.vars["root"] = self.driver.current_window_handle
        self.driver.switch_to.window(self.vars["win8328"])
        self.driver.find_element_by_id("id_order_options-2-order_number").click()
        self.driver.find_element_by_id("id_order_options-2-order_number").clear()
        self.driver.find_element_by_id("id_order_options-2-order_number").send_keys("3")
        self.driver.find_element_by_id("id_order_options-2-option").click()
        self.driver.find_element_by_id("id_order_options-2-option").clear()
        self.driver.find_element_by_id("id_order_options-2-option").send_keys(u"Opcion añadida")
        self.driver.find_element_by_name("_save").click()
        self.vars["window_handles"] = self.driver.window_handles
        self.driver.switch_to.window(self.vars["root"])
        self.driver.find_element_by_xpath("//img[@alt='Change']").click()
        self.vars["win8329"] = self.wait_for_window(2000)
        self.vars["root"] = self.driver.current_window_handle
        self.driver.switch_to.window(self.vars["win8329"])
        self.assertEqual(u"Opcion añadida", self.driver.find_element_by_id("id_order_options-2-option").text)

    def test_view_booth_voting(self):
        User.objects.create_superuser('superuser', 'superuser@decide.com', 'superuser')
        #Proceso para loguearse como administrador
        self.driver.get(f'{self.live_server_url}/admin/')
        time.sleep(1)
        self.driver.find_element_by_id('id_username').send_keys("superuser")
        self.driver.find_element_by_id('id_password').send_keys("superuser", Keys.ENTER)
        #Proceso para añadir una pregunta y sus opciones
        self.assertTrue(len(self.driver.find_elements_by_id('user-tools')) == 1)
        time.sleep(1)
        self.driver.find_element(By.LINK_TEXT, "Votings").click()
        time.sleep(1)
        self.driver.find_element(By.CSS_SELECTOR, ".addlink").click()
        self.driver.find_element_by_id('id_name').send_keys("Voting test")
        self.driver.find_element_by_id('id_desc').send_keys("Test description")
        self.driver.find_element_by_id('id_slug').send_keys("test")
        self.driver.find_element_by_id('id_question').click()
        self.vars["window_handles"] = self.driver.window_handles
        #Proceso para añadir una pregunta y sus opciones
        self.driver.find_element(By.CSS_SELECTOR, "#add_id_question > img").click()
        self.vars["win2433"] = self.wait_for_window(2000)
        self.vars["root"] = self.driver.current_window_handle
        self.driver.switch_to.window(self.vars["win2433"])
        self.driver.find_element(By.ID, "id_desc").click()
        self.driver.find_element(By.ID, "id_desc").send_keys("Question description")
        self.driver.find_element(By.ID, "id_options-0-option").click()
        self.driver.find_element(By.ID, "id_options-0-option").send_keys("Option 1")
        self.driver.find_element(By.ID, "id_options-1-option").click()
        self.driver.find_element(By.ID, "id_options-1-option").send_keys("Option 2")
        self.driver.find_element(By.NAME, "_save").click()
        self.driver.switch_to.window(self.vars["root"])
        #Vuelta a la vista para crear una votación, y creación de un Auth
        self.vars["window_handles"] = self.driver.window_handles
        self.driver.find_element(By.CSS_SELECTOR, "#add_id_auths > img").click()
        self.vars["win1901"] = self.wait_for_window(2000)
        self.driver.switch_to.window(self.vars["win1901"])
        self.driver.find_element(By.ID, "id_name").send_keys("auth")
        self.driver.find_element(By.ID, "id_url").click()
        self.driver.find_element(By.ID, "id_url").send_keys(f'{self.live_server_url}')
        time.sleep(1)
        self.driver.find_element(By.NAME, "_save").click()
        #Proceso para guardar la votación
        self.driver.switch_to.window(self.vars["root"])
        self.driver.find_element(By.NAME, "_save").click()
        time.sleep(1)
        #Iniciamos la votación
        self.driver.find_element(By.NAME, "_selected_action").click()
        self.driver.find_element(By.NAME, "action").click()
        dropdown = self.driver.find_element(By.NAME, "action")
        dropdown.find_element(By.XPATH, "//option[. = 'Start']").click()
        self.driver.find_element(By.CSS_SELECTOR, "option:nth-child(3)").click()
        self.driver.find_element(By.NAME, "index").click()
        self.driver.find_element(By.NAME, "_selected_action").click()
        self.driver.find_element(By.NAME, "action").click()
        time.sleep(1)
        #Comprobamos que se accede a la votación en la cabina con la URL
        self.driver.get(f'{self.live_server_url}/booth/url/test')
        time.sleep(1)
        self.driver.find_element(By.XPATH, "//h1[contains(.,' - Voting test')]")

    def test_view_booth_voting_modified(self):
        User.objects.create_superuser('superuser', 'superuser@decide.com', 'superuser')
        #Proceso para loguearse como administrador
        self.driver.get(f'{self.live_server_url}/admin/')
        time.sleep(1)
        self.driver.find_element_by_id('id_username').send_keys("superuser")
        self.driver.find_element_by_id('id_password').send_keys("superuser", Keys.ENTER)
        #Proceso para añadir una pregunta y sus opciones
        self.assertTrue(len(self.driver.find_elements_by_id('user-tools')) == 1)
        time.sleep(1)
        self.driver.find_element(By.LINK_TEXT, "Votings").click()
        time.sleep(1)
        self.driver.find_element(By.CSS_SELECTOR, ".addlink").click()
        self.driver.find_element_by_id('id_name').send_keys("Voting_test")
        self.driver.find_element_by_id('id_desc').send_keys("Test description")
        self.driver.find_element_by_id('id_slug').send_keys("test")
        self.driver.find_element_by_id('id_question').click()
        self.vars["window_handles"] = self.driver.window_handles
        #Proceso para añadir una pregunta y sus opciones
        self.driver.find_element(By.CSS_SELECTOR, "#add_id_question > img").click()
        self.vars["win2433"] = self.wait_for_window(2000)
        self.vars["root"] = self.driver.current_window_handle
        self.driver.switch_to.window(self.vars["win2433"])
        self.driver.find_element(By.ID, "id_desc").click()
        self.driver.find_element(By.ID, "id_desc").send_keys("Question description")
        self.driver.find_element(By.ID, "id_options-0-option").click()
        self.driver.find_element(By.ID, "id_options-0-option").send_keys("Option 1")
        self.driver.find_element(By.ID, "id_options-1-option").click()
        self.driver.find_element(By.ID, "id_options-1-option").send_keys("Option 2")
        self.driver.find_element(By.NAME, "_save").click()
        self.driver.switch_to.window(self.vars["root"])
        #Vuelta a la vista para crear una votación, y creación de un Auth
        self.vars["window_handles"] = self.driver.window_handles
        self.driver.find_element(By.CSS_SELECTOR, "#add_id_auths > img").click()
        self.vars["win1901"] = self.wait_for_window(2000)
        self.driver.switch_to.window(self.vars["win1901"])
        self.driver.find_element(By.ID, "id_name").send_keys("auth")
        self.driver.find_element(By.ID, "id_url").click()
        self.driver.find_element(By.ID, "id_url").send_keys(f'{self.live_server_url}')
        time.sleep(1)
        self.driver.find_element(By.NAME, "_save").click()
        #Proceso para guardar la votación
        self.driver.switch_to.window(self.vars["root"])
        self.driver.find_element(By.NAME, "_save").click()
        time.sleep(1)
        #Iniciamos la votación
        self.driver.find_element(By.NAME, "_selected_action").click()
        self.driver.find_element(By.NAME, "action").click()
        dropdown = self.driver.find_element(By.NAME, "action")
        dropdown.find_element(By.XPATH, "//option[. = 'Start']").click()
        self.driver.find_element(By.CSS_SELECTOR, "option:nth-child(3)").click()
        self.driver.find_element(By.NAME, "index").click()
        self.driver.find_element(By.NAME, "_selected_action").click()
        self.driver.find_element(By.NAME, "action").click()
        time.sleep(1)
        #Modificamos la URL de la votación creada
        self.driver.find_element(By.XPATH, "//a[contains(.,'Voting_test')]").click()
        self.driver.find_element_by_id('id_slug').clear()
        self.driver.find_element_by_id('id_slug').send_keys("testselenium")
        time.sleep(1)
        self.driver.find_element(By.NAME, "_save").click()
        time.sleep(1)
        #Comprobamos que se accede a la votación en la cabina con la nueva URL
        self.driver.get(f'{self.live_server_url}/booth/url/testselenium')
        time.sleep(1)
        self.driver.find_element(By.XPATH, "//h1[contains(.,' - Voting_test')]")

class OrderVotingTestCase(BaseTestCase):
    def setUp(self):

        q1 = Question(desc='Mock question description')
        q1.save()

        qo1 = QuestionOrder(question = q1, option = 'First option', number=1, order_number=1)
        qo1.save()

        qo2 = QuestionOrder(question = q1, option = 'Second option', number=2, order_number=2)
        qo2.save()

        qo3 = QuestionOrder(question = q1, option = 'Third option', number=3, order_number=3)
        qo3.save()

        self.v=Voting(name="Mock voting",question=q1, slug="testslug1")
        self.v.save()

        super().setUp()

    def tearDown(self):
        super().tearDown()
        self.v=None

    #tests if a order option can be repeated in different order options in a new question
    def test_repeated_order_number(self):
        q2 = Question(desc='Second mock question description')
        q2.save()

        qo21 = QuestionOrder(question = q2, option = 'First option', number=1, order_number=1)
        qo21.save()

        qo22 = QuestionOrder(question = q2, option = 'Second option', number=2, order_number=1)
        qo22.save()

        qo23 = QuestionOrder(question = q2, option = 'Third option', number=3, order_number=1)
        qo23.save()

        self.v2=Voting(name="Second mock voting",question=q2, slug="testslug2")
        self.v2.save()

        self.assertEquals(len(q2.order_options.all()), 3)
        self.assertNotEquals(q2.order_options.all()[0].order_number, q2.order_options.all()[1].order_number)
        self.assertNotEquals(q2.order_options.all()[1].order_number, q2.order_options.all()[2].order_number)

    #tests if a order option can be repeated in different order options in an existing
    def test_repeated_order_number_existing_question(self):
        q1 = Question.objects.get(desc='Mock question description')
        qo4 = QuestionOrder(question = q1, option = 'Third option (repeated)', number=4, order_number=3)
        q1.save()
        qo4.save()

        self.assertEquals(len(q1.order_options.all()), 4)
        self.assertEquals(q1.order_options.all()[3].number, 4)
        self.assertEquals(q1.order_options.all()[3].order_number, 4)