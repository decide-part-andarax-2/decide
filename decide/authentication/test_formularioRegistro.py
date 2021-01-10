from django.test import TestCase
from django.contrib.staticfiles.testing import StaticLiveServerTestCase

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from django.contrib.auth.models import User
from base.tests import BaseTestCase
import itertools
import json
from voting.models import Voting, Question, QuestionOption, QuestionOrder
from django.conf import settings
from mixnet.models import Auth
from django.utils import timezone


class TestFormularioRegistro(StaticLiveServerTestCase):

    def setUp(self):
        #Load base test functionality for decide
        self.base = BaseTestCase()
        self.base.setUp()

        options = webdriver.ChromeOptions()
        options.headless = True
        self.driver = webdriver.Chrome(options=options)

        super().setUp()            
            
    def tearDown(self):           
        super().tearDown()
        self.driver.quit()
        self.base.tearDown()
    	
    # Un usuario se registra y luego se logea correctamente sin 2fa
    def test_registrologinno2fa(self):
        self.driver.get(f'{self.live_server_url}')
        self.driver.set_window_size(1366, 728)
        self.driver.find_element(By.LINK_TEXT, "Regístrate aquí").click()
        self.driver.find_element(By.ID, "id_username").send_keys("usuariono2fa")
        self.driver.find_element(By.ID, "id_password1").click()
        self.driver.find_element(By.ID, "id_password1").send_keys("1234qwer")
        self.driver.find_element(By.ID, "id_password2").click()
        self.driver.find_element(By.ID, "id_password2").send_keys("1234qwer")
        self.driver.find_element(By.ID, "id_phone").click()
        self.driver.find_element(By.ID, "id_phone").send_keys("000000000")
        self.driver.find_element(By.CSS_SELECTOR, ".btn").click()
        assert self.driver.find_element(By.CSS_SELECTOR, "#app-booth > h1").text == "Bienvenido a Decide! USUARIONO2FA"
        self.driver.find_element(By.LINK_TEXT, "logout").click()
        assert self.driver.find_element(By.CSS_SELECTOR, "#app-booth > h1").text == "Inicio de sesión | Decide!"
        self.driver.find_element(By.NAME, "username").click()
        self.driver.find_element(By.NAME, "username").send_keys("usuariono2fa")
        self.driver.find_element(By.NAME, "password").send_keys("1234qwer")
        self.driver.find_element(By.CSS_SELECTOR, ".btn").click()
        assert self.driver.find_element(By.CSS_SELECTOR, "#app-booth > h1").text == "Bienvenido a Decide! USUARIONO2FA"

  #Un usuario no rellena correctamente el formulario de registro, las passwords no coinciden y el teléfono no tiene formato correcto
    def test_formularioRegistroIncorrecto(self):
        self.driver.get(f'{self.live_server_url}')
        self.driver.set_window_size(1366, 728)
        self.driver.find_element(By.LINK_TEXT, "Regístrate aquí").click()
        self.driver.find_element(By.ID, "id_username").send_keys("usuarioerror")
        self.driver.find_element(By.ID, "id_email").click()
        self.driver.find_element(By.ID, "id_email").send_keys("usuario@gmail.com")
        self.driver.find_element(By.ID, "id_password1").click()
        self.driver.find_element(By.ID, "id_password1").send_keys("password1")
        self.driver.find_element(By.ID, "id_password2").click()
        self.driver.find_element(By.ID, "id_password2").send_keys("password2")
        self.driver.find_element(By.ID, "id_phone").click()
        self.driver.find_element(By.ID, "id_phone").send_keys("error")
        self.driver.find_element(By.CSS_SELECTOR, "button").click()
        assert self.driver.find_element(By.CSS_SELECTOR, ".text-danger").text == "The two password fields didn't match."
        assert self.driver.find_element(By.CSS_SELECTOR, ".errorlist > li").text == "El teléfono debe estar formado por 9 dígitos"