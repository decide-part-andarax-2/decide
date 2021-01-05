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
from django.contrib.auth.models import User
from base.tests import BaseTestCase
import itertools
import time
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

    #Un usuario se registra y luego se logea correctamente
    def test_formularioRegistro_login_correcto(self):
        self.driver.get(f'{self.live_server_url}')
        self.driver.set_window_size(1386, 752)
        self.driver.find_element(By.LINK_TEXT, "Regístrate aquí").click()
        assert self.driver.find_element(By.CSS_SELECTOR, "h1").text == "Registro de usuario"
        self.driver.find_element(By.ID, "id_username").click()
        self.driver.find_element(By.ID, "id_username").send_keys("decide2")
        self.driver.find_element(By.ID, "id_first_name").click()
        self.driver.find_element(By.ID, "id_first_name").send_keys("Decide2")
        self.driver.find_element(By.ID, "id_last_name").click()
        self.driver.find_element(By.ID, "id_last_name").send_keys("Decide2")
        self.driver.find_element(By.ID, "id_email").click()
        self.driver.find_element(By.ID, "id_email").send_keys("decide2@gmail.com")
        self.driver.find_element(By.ID, "id_password1").click()
        self.driver.find_element(By.ID, "id_password1").send_keys("hola1234")
        self.driver.find_element(By.ID, "id_password2").click()
        self.driver.find_element(By.ID, "id_password2").send_keys("hola1234")
        self.driver.find_element(By.ID, "id_phone").click()
        self.driver.find_element(By.ID, "id_phone").send_keys("955667895")
        self.driver.find_element(By.ID, "id_double_authentication").click()
        self.driver.find_element(By.CSS_SELECTOR, "button").click()
        assert self.driver.find_element(By.CSS_SELECTOR, "h1").text == "Bienvenido a Decide! DECIDE2"
        self.driver.find_element(By.LINK_TEXT, "Logout").click()
        self.driver.get(f'{self.live_server_url}')
        self.driver.find_element(By.LINK_TEXT, "Login").click()
        self.driver.find_element(By.NAME, "username").click()
        self.driver.find_element(By.NAME, "username").send_keys("decide2")
        self.driver.find_element(By.NAME, "password").click()
        self.driver.find_element(By.NAME, "password").send_keys("hola1234")
        self.driver.find_element(By.NAME, "password").send_keys(Keys.ENTER)
        assert self.driver.find_element(By.CSS_SELECTOR, "h1").text == "Bienvenido a Decide! DECIDE2"
        self.driver.find_element(By.LINK_TEXT, "Logout").click()
        assert self.driver.find_element(By.CSS_SELECTOR, "h1").text == "Inicio de sesión | Decide!"

  #Un usuario no rellena correctamente el formulario de registro, las passwords no coinciden y el teléfono no tiene formato correcto
    def test_formularioRegistroIncorrecto(self):
        self.driver.get(f'{self.live_server_url}')
        self.driver.set_window_size(1386, 752)
        self.driver.find_element(By.LINK_TEXT, "Regístrate aquí").click()
        self.driver.find_element(By.ID, "id_username").click()
        self.driver.find_element(By.ID, "id_username").send_keys("decide2")
        self.driver.find_element(By.ID, "id_first_name").click()
        self.driver.find_element(By.ID, "id_first_name").send_keys("Decide2")
        self.driver.find_element(By.ID, "id_last_name").click()
        self.driver.find_element(By.ID, "id_last_name").send_keys("Decide2")
        self.driver.find_element(By.ID, "id_email").click()
        self.driver.find_element(By.ID, "id_email").send_keys("decide2@gmail.com")
        self.driver.find_element(By.ID, "id_password1").click()
        self.driver.find_element(By.ID, "id_password1").send_keys("hola1234")
        self.driver.find_element(By.ID, "id_password2").click()
        self.driver.find_element(By.ID, "id_password2").send_keys("adios1234")
        self.driver.find_element(By.ID, "id_phone").click()
        self.driver.find_element(By.ID, "id_phone").send_keys("hola")
        self.driver.find_element(By.ID, "id_double_authentication").click()
        self.driver.find_element(By.CSS_SELECTOR, "button").click()
        assert self.driver.find_element(By.CSS_SELECTOR, ".errorlist:nth-child(9) > li").text == "The two password fields didn't match."
        assert self.driver.find_element(By.CSS_SELECTOR, ".errorlist:nth-child(11) > li").text == "El teléfono debe estar formado por 9 dígitos"

#Un usuario hace login con password erroneo
    def test_login_incorrecto(self):
        self.driver.get(f'{self.live_server_url}')
        self.driver.set_window_size(1386, 752)
        self.driver.find_element(By.LINK_TEXT, "Login").click()
        self.driver.find_element(By.NAME, "username").click()
        self.driver.find_element(By.NAME, "username").send_keys("decide")
        self.driver.find_element(By.NAME, "password").click()
        self.driver.find_element(By.NAME, "password").send_keys("hola1234")
        self.driver.find_element(By.NAME, "password").send_keys(Keys.ENTER)
        assert self.driver.find_element(By.CSS_SELECTOR, "h1").text == "Inicio de sesión | Decide!"



        
        

