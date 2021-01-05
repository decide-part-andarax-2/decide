
from django.test import TestCase
from django.contrib.staticfiles.testing import StaticLiveServerTestCase

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions
from django.contrib.auth.models import User
from base.tests import BaseTestCase
import itertools
import time
from voting.models import Voting, Question, QuestionOption, QuestionOrder
from authentication.models import Extra
from django.conf import settings
from mixnet.models import Auth
from django.utils import timezone
import logging
import pyotp

class Login2FA(StaticLiveServerTestCase):

    def create_voting(self):
        self.q = Question(desc='Prueba votación')
        self.q.save()
        for i in range(2):
            opt = QuestionOption(question=self.q, option='Opción {}'.format(i+1))
            opt.save()
        self.v= Voting(name='Prueba votación', question=self.q, link="prueba")
        self.v.save()
        self.a, _ = Auth.objects.get_or_create(url=settings.BASEURL,defaults={'me': True, 'name': 'test auth'})
        self.a.save()
        self.v.auths.add(self.a)
        self.v.create_pubkey()
        self.v.start_date = timezone.now()
        self.v.save()
        
    def createUsers(self):
        self.user_with_2fa = User(username='userfa')
        self.user_with_2fa.set_password('qwerty')
        self.user_with_2fa.save()

        self.user_no_2fa = User(username="usernofa")
        self.user_no_2fa.set_password('qwerty')
        self.user_no_2fa.save()

        self.extra = Extra(phone='020304050')
        self.extra.totp_code = 'S3K3TPI5MYA2M67V'
        self.extra.user = self.user_with_2fa
        self.extra.save()
        totp_code = pyotp.TOTP(self.extra.totp_code).now()


    def setUp(self):

        self.base = BaseTestCase()
        self.base.setUp()

        self.vars = {}
        self.create_voting()
        self.createUsers()
        options = webdriver.ChromeOptions()
        options.headless = True
        self.driver = webdriver.Chrome(options=options)

        super().setUp()

    def tearDown(self):
        super().tearDown()
        self.driver.quit()
        self.base.tearDown()
        self.v.delete()

    #Un usuario con 2fa no puede logearse si no lo introduce
    def test_login2faWithoutIt(self):
        self.driver.get(f'{self.live_server_url}/booth/{self.v.pk}')
        self.driver.set_window_size(1366, 728)
        self.driver.find_element(By.ID, "username").click()
        self.driver.find_element(By.ID, "username").send_keys("user2fa")
        self.driver.find_element(By.ID, "password").click()
        self.driver.find_element(By.ID, "password").send_keys("qwerty")
        self.driver.find_element(By.CSS_SELECTOR, ".btn").click()
        assert self.driver.find_element(By.ID, "__BVID__11__BV_label_").text == "Username"

    #Un usuario sin 2fa puede logearse bien
    def test_logino2fa(self):
        self.driver.get(f'{self.live_server_url}/booth/{self.v.pk}')
        self.driver.set_window_size(1366, 728)
        # self.driver.find_element(By.ID, "__BVID__19__BV_label_").click()
        self.driver.find_element(By.ID, "username").click()
        self.driver.find_element(By.ID, "username").send_keys("usernofa")
        self.driver.find_element(By.ID, "password").send_keys("qwerty")
        self.driver.find_element(By.CSS_SELECTOR, ".btn").click()
        elements = self.driver.find_elements(By.CSS_SELECTOR, ".btn")
        assert len(elements) > 0

    #Un usuario sin 2fa no puede logearse en el formulario para 2fa
    def test_loginno2fain2fa(self):
        self.driver.get(f'{self.live_server_url}/booth/{self.v.pk}')
        self.driver.set_window_size(1366, 728)
        self.driver.find_element(By.CSS_SELECTOR, ".custom-control:nth-child(2) > .custom-control-label").click()
        self.driver.find_element(By.ID, "username").click()
        self.driver.find_element(By.ID, "username").send_keys("usuarionofa")
        self.driver.find_element(By.ID, "password").send_keys("qwerty")
        self.driver.find_element(By.CSS_SELECTOR, ".btn").click()
        assert self.driver.find_element(By.ID, "__BVID__11__BV_label_").text == "Username"