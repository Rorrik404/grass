from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common import NoSuchElementException, ElementNotInteractableException

from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType

from selenium.common.exceptions import WebDriverException, NoSuchDriverException

import logging
from telegram.ext import Application
import asyncio


import time
import requests
import os
import re
import base64
from flask import Flask
import hashlib
import sys

# Setup env variables
ALLOW_DEBUG = os.getenv('ALLOW_DEBUG', 'False').strip().lower() == 'true'
print (ALLOW_DEBUG)

# Create a logger
logger = logging.getLogger(__name__)

# Set the logging level
logger.setLevel(logging.DEBUG if ALLOW_DEBUG else logging.ERROR)

# Create a formatter
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# Create a file handler
file_handler = logging.FileHandler('app.log')
file_handler.setFormatter(formatter)

# Create a console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

# Add handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

if ALLOW_DEBUG == True:
    logger.debug('Debugging is enabled! This will generate a screenshot and console logs on error!')

BOT_TOKEN = '7776316269:AAES2yNl__LEAsFJDIlxcK0ZytLwX-oO5Co'
GROUPID = -4026028372
extensionId = 'ilehaonighjijnmpnagapkhpcdbhclfg'
CRX_URL = "https://clients2.google.com/service/update2/crx?response=redirect&prodversion=98.0.4758.102&acceptformat=crx2,crx3&x=id%3D~~~~%26uc&nacl_arch=x86-64"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36"


# Function to send a photo to a specific chat and then disconnect
async def send_photo_to_chat(photo_path: str) -> None:
    # Create the Application and pass it your bot's token
    application = Application.builder().token(BOT_TOKEN).build()

    # Send the photo
    async with application:
        await application.bot.send_photo(chat_id=GROUPID, photo=open(photo_path, 'rb'))


# Function to send a message to a specific chat and then disconnect
async def send_message_to_chat(message: str) -> None:
    # Create the Application and pass it your bot's token
    application = Application.builder().token(BOT_TOKEN).build()

    # Send the message
    async with application:
        await application.bot.send_message(chat_id=GROUPID, text=message)


# Function to send a file to a specific chat and then disconnect
async def send_file_to_chat(file_path: str) -> None:
    # Create the Application and pass it your bot's token
    application = Application.builder().token(BOT_TOKEN).build()

    # Send the document (file)
    async with application:
        await application.bot.send_document(chat_id=GROUPID, document=open(file_path, 'rb'))


logger.debug('Starting...')
try:
    if ALLOW_DEBUG == True:
        logger.debug('GRASS_USER: ' + os.environ['GRASS_USER'])
        logger.debug('GRASS_PASS: ' + os.environ['GRASS_PASS'])
    USER = os.environ['GRASS_USER']
    PASSW = os.environ['GRASS_PASS']
except:
    USER = ''
    PASSW = ''



# are they set?
if USER == '' or PASSW == '':
    logger.error('Please set GRASS_USER and GRASS_PASS env variables')
    exit()


#https://gist.github.com/ckuethe/fb6d972ecfc590c2f9b8
def download_extension(extension_id):
    url = CRX_URL.replace("~~~~", extension_id)
    headers = {"User-Agent": USER_AGENT}
    r = requests.get(url, stream=True, headers=headers)
    with open("grass.crx", "wb") as fd:
        for chunk in r.iter_content(chunk_size=128):
            fd.write(chunk)
    if ALLOW_DEBUG == True:
        #generate md5 of file
        md5 = hashlib.md5(open('grass.crx', 'rb').read()).hexdigest()
        logger.debug('Extension MD5: ' + md5)

def generate_error_report(driver):
    if ALLOW_DEBUG == False:
        return
    #grab screenshot
    driver.save_screenshot('error.png')
    #grab console logs
    logs = driver.get_log('browser')
    with open('error.log', 'w') as f:
        for log in logs:
            f.write(str(log))
            f.write('\n')

    # Send the photo and disconnect
    asyncio.run(send_photo_to_chat('error.png'))


def get_html_data():
    html_data = driver.page_source
    with open('page_data.html', 'w', encoding='utf-8') as file:
        file.write(html_data)
    return 'page_data.html'    

logger.debug('Downloading extension...')
download_extension(extensionId)
logger.debug('Downloaded! Installing extension and driver manager...')

options = webdriver.ChromeOptions()
#options.binary_location = '/usr/bin/chromium-browser'
options.add_argument("--headless=new")
options.add_argument("--disable-dev-shm-usage")
options.add_argument('--no-sandbox')
options.add_argument("window-size=1920x1080")

options.add_extension('grass.crx')

logger.debug('Installed! Starting...')
try:
    driver = webdriver.Chrome(options=options)
except (WebDriverException, NoSuchDriverException) as e:
    logger.debug('Could not start with Manager! Trying to default to manual path...')
    try:
        driver_path = "/usr/bin/chromedriver"
        service = ChromeService(executable_path=driver_path)
        driver = webdriver.Chrome(service=service, options=options)
    except (WebDriverException, NoSuchDriverException) as e:
        logger.error('Could not start with manual path! Exiting...')
        exit()

#driver.get('chrome-extension://'+extensionId+'/index.html')
logger.debug('Loading dashboard...')
driver.get('https://app.getgrass.io/')

# Define a wait with a timeout of 10 seconds

wait = WebDriverWait(driver, 10)

try:
    logger.debug('Checking for Accept All...')    
    wait.until(EC.presence_of_element_located((By.XPATH, "//button[text()='ACCEPT ALL']"))).click()
except:
    logger.debug('Could not find Accept All...continuing...')    

try:
    logger.debug('Waiting for login form...')
    wait.until(EC.presence_of_element_located((By.XPATH, '//*[@name="user"]'))).send_keys(USER)
    logger.debug('User populated!')
    wait.until(EC.presence_of_element_located((By.XPATH, '//*[@name="password"]'))).send_keys(PASSW)
    logger.debug('Password populated!')
    wait.until(EC.presence_of_element_located((By.XPATH, '//*[@type="submit"]'))).click()
    logger.debug('Login button clicked!')
except:
    logger.error('Could not populate login form! Exiting...')
    generate_error_report(driver)
    driver.quit()
    exit()

try:
    wait.until(EC.presence_of_element_located((By.XPATH, '//*[contains(text(), "Dashboard")]')))
except:
    logger.error('Could not login! Double Check your username and password! Exiting...')
    generate_error_report(driver)
    driver.quit()
    exit()



logger.debug('Logged in! Waiting for connection...')
driver.get('chrome-extension://'+extensionId+'/index.html')
try:
    wait.until(EC.presence_of_element_located((By.XPATH, '//*[contains(text(), "Desktop dashboard")]')))
    logger.debug('Connected!')
except:
    logger.error('Could not load connection! Exiting...')
    generate_error_report(driver)
    driver.quit()
    exit()

logger.debug('Starting API...')
#flask api
app = Flask(__name__)

@app.route('/status', methods=['GET'])
def status():
    logger.debug('Getting network quality...')
    try:
        # Find the "Network Quality" text label
        network_quality_label =  wait.until(EC.presence_of_element_located((By.XPATH, "//p[contains(text(), 'Network Quality')]")))
        # Now find the following <p> element that contains the percentage value
        network_quality_percent = network_quality_label.find_element(By.XPATH, "following-sibling::p").text
        # Get the text value
        network_quality = re.findall(r'\d+', network_quality_percent)[0]
    except Exception as e:
        network_quality = False
        logger.error('Could not get network quality!')
        generate_error_report(driver)

    logger.debug('Getting earnings...')
    try:
        # Find the <img> tag with the alt attribute "token"
        token_image = wait.until(EC.presence_of_element_located((By.XPATH, "//img[@alt='token']")))
        # Now find the next sibling div that contains the earnings value
        epoch_earnings = token_image.find_element(By.XPATH, "following-sibling::div/p").text
    except Exception as e:
        epoch_earnings = False
        logger.debug('Could not get earnings!')
        generate_error_report(driver)
    
    logger.debug('Getting connection status...')
    try:
        status_element = driver.find_elements(By.XPATH, '//*[contains(text(), "Grass is Connected")]')
        connected = True
    except Exception as e:
        connected = False
        logger.error('Could not get confirmation of connection!')
        generate_error_report(driver)

    return {'connected': connected, 'network_quality': network_quality, 'epoch_earnings': epoch_earnings}


@app.route('/showme', methods=['GET'])
def showme():
    #grab screenshot
    driver.save_screenshot('error.png')
    # Send the photo and disconnect
    asyncio.run(send_photo_to_chat('error.png')) 
    #grab console logs
    asyncio.run(send_file_to_chat(get_html_data()))
    
    return {'Status':'Data Sent!'}

app.run(host='0.0.0.0',port=80, debug=ALLOW_DEBUG, use_reloader=False)
driver.quit()