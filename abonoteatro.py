import json
import logging
import smtplib
import time

from email.mime.text import MIMEText
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from utils import Config, Logger

Logger()
logger = logging.getLogger('server')
config = Config()

ini_tt = time.time()
logger.info("Start web scrapping")
chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("--disable-gpu")
prefs = { "profile.default_content_setting_values.geolocation": 2 }     # 1 allow, 2 block
chrome_options.add_argument("--disable-notifications")
chrome_options.add_experimental_option("prefs", prefs)
driver = webdriver.Chrome(options=chrome_options)
driver.get(config.get('abonoteatro_url'))

# Close cookies
WebDriverWait(driver, 10)\
    .until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Aceptar cookies')]"))).click()

# Fill login form
WebDriverWait(driver, 10).until(EC.visibility_of_element_located(
    (By.XPATH, "//input[@id='nabonadologin']"))).send_keys(config.get('abonoteatro_user'))
driver.find_element("xpath", "//input[@id='contrasenalogin']").send_keys(config.get('abonoteatro_password'))
driver.find_element("xpath", "//input[@value='Entrar']").click()

# Wait for page change and complete
time.sleep(2)
while driver.execute_script("return document.readyState") != "complete":
    time.sleep(0.5)

# Get events
WebDriverWait(driver, 10).until(EC.frame_to_be_available_and_switch_to_it((By.XPATH, "//iframe")))
container = WebDriverWait(driver, 10).until(EC.visibility_of_element_located(
    (By.XPATH, "//div[@class='main-content container']")))
elements = container.find_elements("xpath", "//div[@class='row']")
events = []
for element in elements:
    content = element.text
    tokens = element.text.splitlines()
    if len(tokens) >= 5:
        title = tokens[0].upper()
        if title != 'FECHA EVENTO':
            subtitle = tokens[1].upper() if len(tokens) == 6 else ''
            location = tokens[-4].upper()
            if "MÁLAGA" not in location:
                price = float(tokens[-2][:-1].replace(',', '.'))
                events.append({'title': title, 'subtitle': subtitle, 'location': location, 'price': price})
driver.close()
events = sorted(events, key=lambda e: e['title'])
events = sorted(events, key=lambda e: e['price'], reverse=True)

# Load old events
with open(config.get('events_file')) as input_file:
    old_events = json.load(input_file)

# Find new events
active_events = {}
new_events = []
for event in events:
    active_events[event['title']] = event
    if event['price'] >= config.get('events_threshold') and event['title'] not in old_events:
        new_events.append(event)

# Send new events by email
if len(new_events) > 0:
    logger.info(f"Notify {len(new_events)} new events")
    mail_tittle = "Novedades Abonoteatro"
    body = f"{mail_tittle}:\n"
    for event in new_events:
        body += f"* {event['title']}, {event['subtitle']}, {event['location']}, {event['price']}\n"
    msg = MIMEText(body)
    msg['Subject'] = mail_tittle
    msg['From'] = config.get('gmail_user')
    msg['To'] = ', '.join(config.get('gmail_recipients'))
    with smtplib.SMTP_SSL(config.get('gmail_server'), config.get('gmail_port')) as server:
        server.login(config.get('gmail_user'), config.get('gmail_password'))
        server.sendmail(config.get('gmail_user'), config.get('gmail_recipients'), msg.as_string())

# Store events in file
with open(config.get('events_file'), 'w') as outfile:
    json.dump(active_events, outfile)
logger.info(f"{len(active_events)} events found in {round(time.time() - ini_tt, 2)} seconds")
