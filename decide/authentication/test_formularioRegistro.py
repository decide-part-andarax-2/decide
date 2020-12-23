# Generated by Selenium IDE
'''
import pytest
import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

class TestFormularioRegistro():
  def setup_method(self, method):
    self.driver = webdriver.Chrome()
    self.vars = {}
  
  def teardown_method(self, method):
    self.driver.quit()
  
  def test_formularioRegistro(self):
    self.driver.get("http://127.0.0.1:8000/")
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
  
'''