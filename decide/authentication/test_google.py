from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from base.tests import BaseTestCase
from voting.models import Voting, Question, QuestionOption
from django.conf import settings
from mixnet.models import Auth
from django.utils import timezone
import geckodriver_autoinstaller

geckodriver_autoinstaller.install()

class TestGoogle(StaticLiveServerTestCase):


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
    

    def setUp(self):

        self.base = BaseTestCase()
        self.base.setUp()        
        self.vars = {}
        self.create_voting()
        options = webdriver.ChromeOptions()
        options.headless = True
        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 10)
        self.driver.maximize_window()
        self.driver.implicitly_wait(10)
        
        self.driver = webdriver.Firefox()
        
        super().setUp()

    def tearDown(self):
        super().tearDown()
        self.driver.quit()
        self.base.tearDown()
        self.v.delete()
  
    def test_google(self):
                
        self.driver.get(f'{self.live_server_url}/booth/{self.v.pk}')
        assert self.driver.find_element(By.CSS_SELECTOR, ".voting > h1").text[-1] == f"{self.v.pk}"        
        self.driver.find_element(By.LINK_TEXT, "Login con Google").click()
         
         #introducir un email mal
        self.driver.find_element(By.ID, "identifierId").send_keys("test")
        self.driver.find_element(By.ID, "identifierId").send_keys(Keys.ENTER)
        self.driver.find_element(By.ID, "identifierId").send_keys(Keys.BACKSPACE)  
        self.driver.find_element(By.ID, "identifierId").send_keys(Keys.BACKSPACE)  
        self.driver.find_element(By.ID, "identifierId").send_keys(Keys.BACKSPACE) 
        self.driver.find_element(By.ID, "identifierId").send_keys(Keys.BACKSPACE)
        
        # introducir un email que si existe
        self.driver.find_element(By.ID, "identifierId").send_keys("multimediajulian@gmail.com")
        self.driver.find_element(By.ID, "identifierId").send_keys(Keys.ENTER)
        
        #ya no se puede seguir mas por ofuscacion de CSS y HTML
