from django.test import TestCase
from django.contrib.staticfiles.testing import StaticLiveServerTestCase

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

from base.tests import BaseTestCase


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
