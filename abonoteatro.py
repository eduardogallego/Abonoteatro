import logging
import smtplib

from datetime import datetime
from email.mime.text import MIMEText
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from utils import Config, Logger

Logger()
logger = logging.getLogger('server')
config = Config()

logger.info("Start")
service = Service(executable_path='./chromedriver')
options = webdriver.ChromeOptions()
options.add_argument("--headless=new")
driver = webdriver.Chrome(options=options, service=service)
driver.get(config.get('abonoteatro_url'))

logger.info("Close cookies")
WebDriverWait(driver, 10)\
    .until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Aceptar cookies')]"))).click()

logger.info("Fill login form")
WebDriverWait(driver, 10).until(EC.visibility_of_element_located(
    (By.XPATH, "//input[@id='nabonadologin']"))).send_keys(config.get('abonoteatro_user'))
driver.find_element("xpath", "//input[@id='contrasenalogin']").send_keys(config.get('abonoteatro_password'))
driver.find_element("xpath", "//input[@value='Entrar']").click()

logger.info("Get data")
WebDriverWait(driver, 10).until(EC.frame_to_be_available_and_switch_to_it((By.XPATH, "//iframe")))
container = WebDriverWait(driver, 10).until(EC.visibility_of_element_located(
    (By.XPATH, "//div[@class='main-content container']")))
elements = container.find_elements("xpath", "//div[@class='row']")

logger.info("Post process")
events = []
for element in elements:
    content = element.text
    tokens = element.text.splitlines()
    event = {'title': tokens[0].upper(),
             'subtitle': tokens[1].upper() if len(tokens) == 6 else '',
             'location': tokens[-4].upper(),
             'prize': float(tokens[-2][:-1].replace(',', '.'))}
    events.append(event)
driver.close()
events = sorted(events, key=lambda e: e['title'])
events = sorted(events, key=lambda e: e['prize'], reverse=True)

# Send email
logger.info("Send email")
mail_tittle = "Novedades Abonoteatro"
body = f"{mail_tittle}:\n"
for event in events:
    body += f"* {event['title']}, {event['subtitle']}, {event['location']}, {event['prize']}\n"
msg = MIMEText(body)
msg['Subject'] = mail_tittle
msg['From'] = config.get('gmail_user')
msg['To'] = ', '.join(config.get('gmail_recipients'))
with smtplib.SMTP_SSL(config.get('gmail_server'), config.get('gmail_port')) as server:
    server.login(config.get('gmail_user'), config.get('gmail_password'))
    server.sendmail(config.get('gmail_user'), config.get('gmail_recipients'), msg.as_string())

logger.info("End")
