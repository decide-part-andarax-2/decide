
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
from django.conf import settings
from mixnet.models import Auth
from django.utils import timezone
import logging
import geckodriver_autoinstaller

geckodriver_autoinstaller.install()


class Github(StaticLiveServerTestCase):

    def create_voting(self):
        self.q = Question(desc='Prueba votación')
        self.q.save()
        for i in range(2):
            opt = QuestionOption(question=self.q, option='Opción {}'.format(i+1))
            opt.save()
        self.v= Voting(name='Prueba votación', question=self.q, slug="prueba")
        self.v.save()
        self.a, _ = Auth.objects.get_or_create(url=settings.BASEURL,defaults={'me': True, 'name': 'test auth'})
        self.a.save()
        self.v.auths.add(self.a)
        self.v.create_pubkey()
        self.v.start_date = timezone.now()
        self.v.save()

    def setUp(self):

        self.base = BaseTestCase()
        self.base.setUp()
        self.vars = {}
        self.create_voting()
        options = webdriver.ChromeOptions()
        options.headless = True
        self.driver = webdriver.Chrome(options=options)

        self.driver = webdriver.Firefox()
                
        super().setUp()

    def tearDown(self):
        super().tearDown()
        self.driver.quit()
        self.base.tearDown()
        self.v.delete()

    ''' 
    #Sólo se ejecuta correctamente en local
    def test_login_correcto_github(self):
        #Redirección a la votación creada
        self.driver.get(f'{self.live_server_url}/booth/{self.v.pk}')
        assert self.driver.find_element(By.CSS_SELECTOR, ".voting > h1").text == f"{self.v.pk} - Prueba votación"
        #Inicio sesión con github
        self.driver.find_element(By.LINK_TEXT, "Login con GitHub").click()
        self.driver.find_element(By.CSS_SELECTOR, "p:nth-child(2)").click()
        assert self.driver.find_element(By.CSS_SELECTOR, "strong:nth-child(3)").text == "AuthenticationApp"
        self.driver.find_element(By.ID, "login_field").click()
        self.driver.find_element(By.ID, "login_field").send_keys("decideautenticacion")
        self.driver.find_element(By.ID, "password").click()
        self.driver.find_element(By.ID, "password").send_keys("pruebadecide11")
        self.driver.find_element(By.NAME, "commit").click()
        #Esperamos 4 segundos debido a las diferentes redirecciones hasta llegar de nuevo a la página de votación
        time.sleep(3)
        assert self.driver.find_element(By.CSS_SELECTOR, ".btn").text == "Vote"
    '''
    #Usuario introduce una contraseña incorrecta de su cuenta de Github
    def test_login_incorrect_password(self):
        #Redirección a la votación creada
        self.driver.get(f'{self.live_server_url}/booth/{self.v.pk}')
        assert self.driver.find_element(By.CSS_SELECTOR, ".voting > h1").text == f"{self.v.pk} - Prueba votación"
        #Inicio sesión con github
        self.driver.find_element(By.LINK_TEXT, "Login con GitHub").click()
        self.driver.find_element(By.CSS_SELECTOR, "p:nth-child(2)").click()
        assert self.driver.find_element(By.CSS_SELECTOR, "strong:nth-child(3)").text == "AuthenticationApp"
        self.driver.find_element(By.ID, "login_field").click()
        self.driver.find_element(By.ID, "login_field").send_keys("decideautenticacion")
        self.driver.find_element(By.ID, "password").click()
        self.driver.find_element(By.ID, "password").send_keys("1234")
        self.driver.find_element(By.NAME, "commit").click()
        #Mensaje error
        assert self.driver.find_element(By.CSS_SELECTOR, ".flash > .container-lg").text == "Incorrect username or password."

    #Usuario introduce un username incorrecto de su cuenta de Github
    def test_login_incorrect_username(self):
        #Redirección a la votación creada
        self.driver.get(f'{self.live_server_url}/booth/{self.v.pk}')
        assert self.driver.find_element(By.CSS_SELECTOR, ".voting > h1").text == f"{self.v.pk} - Prueba votación"
        #Inicio sesión con github
        self.driver.find_element(By.LINK_TEXT, "Login con GitHub").click()
        self.driver.find_element(By.CSS_SELECTOR, "p:nth-child(2)").click()
        assert self.driver.find_element(By.CSS_SELECTOR, "strong:nth-child(3)").text == "AuthenticationApp"
        self.driver.find_element(By.ID, "login_field").click()
        self.driver.find_element(By.ID, "login_field").send_keys("decideautenticacionn")
        self.driver.find_element(By.ID, "password").click()
        self.driver.find_element(By.ID, "password").send_keys("pruebadecide11")
        self.driver.find_element(By.NAME, "commit").click()
        #Mensaje error
        assert self.driver.find_element(By.CSS_SELECTOR, ".flash > .container-lg").text == "Incorrect username or password."
 

    
        

    
     
        
