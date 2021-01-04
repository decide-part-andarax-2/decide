from base import mods
from django.contrib.auth.models import User
from django.core import mail
from django.contrib.staticfiles.testing import StaticLiveServerTestCase

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from base.tests import BaseTestCase
from freezegun import freeze_time

import re

class AdminTestCase(StaticLiveServerTestCase):

    def setUp(self):
        # Load base test functionality for decide
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

    def test_simpleCorrectLogin(self):
        self.driver.get(f'{self.live_server_url}/admin/')
        self.driver.find_element_by_id('id_username').send_keys("admin")
        self.driver.find_element_by_id('id_password').send_keys("qwerty", Keys.ENTER)

        # print(self.driver.current_url)
        # In case of a correct loging, a element with id 'user-tools' is shown in the upper right part
        self.assertTrue(len(self.driver.find_elements_by_id('user-tools')) == 1)

    def test_simpleWrongLogin(self):
        self.driver.get(f'{self.live_server_url}/admin/')
        self.driver.find_element_by_id('id_username').send_keys("WRONG")
        self.driver.find_element_by_id('id_password').send_keys("WRONG")
        self.driver.find_element_by_id('login-form').submit()
        
        # In case a incorrect login, a div with class 'errornote' is shown in red!
        self.assertTrue(len(self.driver.find_elements_by_class_name('errornote')) == 1)


class EmailAuthRedirectCase(StaticLiveServerTestCase):
    
    @freeze_time('2020-10-10 03:00:00')
    def prepareEmailToken(self):
        self.user_with_email = User(username='userWithEmail')
        self.user_with_email.set_password('qwerty')
        self.user_with_email.email = 'userWithEmail@example.com'
        self.user_with_email.save()

        data = {'email': self.user_with_email.email, 'callback': 'http://dominio.prueba/callback'}
        response = mods.post('authentication/email-generate-token', json=data, response=True)
        self.assertEqual(response.status_code, 200)

        htmlText = mail.outbox[0].alternatives[0][0]
        self.link = re.search(r'href="http://testserver/?([^\'" >]+)', htmlText).group(1)

    def setUp(self):
        # Load base test functionality for decide
        self.base = BaseTestCase()
        self.base.setUp()

        self.prepareEmailToken()

        options = webdriver.ChromeOptions()
        options.headless = True
        self.driver = webdriver.Chrome(options=options)


        super().setUp()

    def tearDown(self):
        super().tearDown()
        self.driver.quit()

        self.base.tearDown()

    @freeze_time('2020-10-10 03:15:00')
    def test_confirmEmailTokenAfterStart(self):
        self.driver.get(f'{self.live_server_url}/{self.link}')

        self.assertEqual(self.driver.current_url, 'http://dominio.prueba/callback')

    @freeze_time('2020-10-10 03:59:00')
    def test_confirmEmailTokenBeforeEnd(self):
        self.driver.get(f'{self.live_server_url}/{self.link}')

        self.assertEqual(self.driver.current_url, 'http://dominio.prueba/callback')

    @freeze_time('2020-10-10 04:01:00')
    def test_confirmEmailTokenAfterEnd(self):
        self.driver.get(f'{self.live_server_url}/{self.link}')
        
        self.assertEqual(self.driver.find_element(By.XPATH, "//div/h1").text, "Error")
        self.assertEqual(self.driver.find_element(By.XPATH, "//div/p").text, "Token is wrong.")

    @freeze_time('2020-10-10 03:30:00')
    def test_confirmEmailTokenInvalidUserId(self):
        self.driver.get(f'{self.live_server_url}/authentication/email-confirm-token/11111/222222/')

        self.assertEqual(self.driver.find_element(By.XPATH, "//div/h1").text, "Error")
        self.assertEqual(self.driver.find_element(By.XPATH, "//div/p").text, "Token is wrong.")

    @freeze_time('2020-10-10 03:30:00')
    def test_confirmEmailTokenInvalidToken(self):
        self.driver.get(f'{self.live_server_url}/authentication/email-confirm-token/{self.user_with_email.pk}/111111/')

        self.assertEqual(self.driver.find_element(By.XPATH, "//div/h1").text, "Error")
        self.assertEqual(self.driver.find_element(By.XPATH, "//div/p").text, "Token is wrong.")