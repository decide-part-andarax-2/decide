import random
import itertools
import time
import os
import tarfile

from django.utils import timezone
from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework.test import APITestCase
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
        v = Voting(name='test voting', question=q, link="prueba")
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

        self.assertTrue(os.path.exists("voting/results.tar"))
        tarfl = tarfile.open("voting/results.tar", "r")
        name = "voting/v" + str(v.id) + ".txt"
        self.assertTrue(name in tarfl.getnames())

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
            'link': 'example',
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
            'link': 'example',
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
        q=Question(desc="Esta es la descripcion")
        q.save()

        opt1=QuestionOption(question=q,option="opcion1")
        opt2=QuestionOption(question=q,option="opcion2")
        opt1.save()
        opt2.save()

        self.v=Voting(name="Votacion",question=q, link="link1")
        self.v.save()

        q2=Question(desc="Segunda Pregunta")
        q2.save()

        q2_opt1=QuestionOption(question=q2,option="primera opcion")
        q2_opt2=QuestionOption(question=q2,option="segunda opcion")
        q2_opt1.save()
        q2_opt2.save()

        self.v2=Voting(name="Segunda Votacion",question=q2, link="link2")
        self.v2.save()
        super().setUp()

    def tearDown(self):
        super().tearDown()
        self.v=None
        self.v2=None

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
        self.driver.find_element_by_id('id_link').send_keys("seleniumtest")
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
        self.driver.find_element_by_id('id_link').send_keys("seleniumtest")
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
        self.driver.find_element_by_id('id_link').send_keys("seleniumtest")
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
        self.driver.find_element_by_id('id_link').send_keys("seleniumtest")
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
        self.driver.find_element_by_id('id_link').send_keys("seleniumtest")
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
        self.vars["win8328"] = self.wait_for_window(2000)
        self.vars["root"] = self.driver.current_window_handle
        self.driver.switch_to.window(self.vars["win8328"])
        self.assertEqual(u"Opcion añadida", self.driver.find_element_by_id("id_order_options-2-option").text)