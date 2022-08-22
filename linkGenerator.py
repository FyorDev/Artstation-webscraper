import sys
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import requests

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

# Loads the driver, not in headless mode because then images won't load
options = webdriver.ChromeOptions()
#options.add_argument('--disable-dev-shm-usage')
driver = webdriver.Chrome(options=options)

# If an argument was given take the link, otherwise default to my profile
if len(sys.argv) >= 2:
    link = str(sys.argv[1])
    print("Opening: " + str(sys.argv[1]))
else:
    link = "https://www.artstation.com/(your name)/following"
    print("Opening default link")

def scrolldown(int):
    i = 0
    amount_of_scroll_down_attempts = int
    # Scrolls to the bottom of the page, ensuring that all images are loaded in.
    while i < amount_of_scroll_down_attempts:
        driver.execute_script(
            "window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(0.1)
        i = i + 1
    return

def links():
    links_to_images = driver.find_elements(By.CLASS_NAME, "users-grid-name")

    print(len(links_to_images), " links found")
    print(links_to_images)
    # Initiates list
    links_list = []

    # Get all links to artworks in profile
    for link in links_to_images:
        if link.find_element(By.CLASS_NAME, "text-white").get_attribute('href') not in links_list:
            links_list.append(link.find_element(By.CLASS_NAME, "text-white").get_attribute('href'))
    return links_list


# Open the link
driver.get(link)
print("Opened webpage")
# Wait for it to load and scroll down
time.sleep(2)
scrolldown(50)

links_list = links()
print(str(len(links_list)) + "links to write found")
print(links_list)

workingDir = os.getcwd()

with open(workingDir + "/links.txt", "w") as outfile:
    outfile.write('\n'.join(links_list) + '\n')


driver.close()
driver.quit()