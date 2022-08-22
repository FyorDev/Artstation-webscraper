#import requests
#import pandas
#import bs4
import sys
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
#import urllib.request
import time
import requests

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

# Loads the driver, not in headless mode because then images won't load
options = webdriver.ChromeOptions()
options.add_argument('--dns-prefetch-disable')
options.add_argument('--disable-dev-shm-usage')
driver = webdriver.Chrome(options=options)


# If an argument was given take the link, otherwise get everything from .txt
if len(sys.argv) >= 2:
    inputlinks = [str(sys.argv[1])]  
    print(str(len(inputlinks)) + " links" )
else:
    with open(os.getcwd() + "/links.txt") as my_file:
        inputlinks = my_file.readlines()
    inputlinks = [s.strip() for s in inputlinks]
    print(str(len(inputlinks)) + " links" )
    

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
    links_to_images = driver.find_elements(By.CLASS_NAME, "project-image")
    # Initiates list
    links_list = []

    # Get all links to artworks in profile
    for link in links_to_images:
        if link.get_attribute('href') not in links_list:
            links_list.append(link.get_attribute('href'))
    return links_list



def scrape(link):



    # Open the link
    driver.get(link + "/albums/all")
    print("Opened webpage")
    # Wait for it to load and scroll down
    time.sleep(2)
    scrolldown(50)

    # Prepare folder
    artistName =  driver.find_element(By.CLASS_NAME, "artist-name").text
    dirName = link.replace("https://www.artstation.com/", '')
    workingDir = os.getcwd() + "/Artists/" + artistName + " " + dirName

    if not os.path.exists(workingDir):
        os.mkdir(workingDir)
        print("Created " + workingDir)
    else:
        print("Folder already exists, skipping makedir for: " + workingDir)

    links_list = links()

    count = 0
    for link in links_list:
        print("Opening " + link)
        driver.get(link)
        try:
            print("Loading...")
            myElem = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, "//div[@class=\"asset-image\"]/picture/img")))
            print("Link loaded")
            # Finds the elements with the class artwork-image.
            images = driver.find_elements(By.XPATH, "//div[@class=\"asset-image\"]/picture/img")
            #images = driver.find_elements(By.XPATH, "//div[@class=\"artwork-image\"]/picture/img")
            print(str(len(images)) + " images found")

            for image in images:
                src = image.get_attribute("src")
                # Strips the query on the right of the filename.
                filename = str(src).strip("1234567890?")
                print("found image: " + src)
                # the path length is different depending on if it is a .gif file or not.
                if filename.endswith(".gif"):
                    print("is a gif, skipping because fuck those")
                    continue
                else:
                    filename = filename[69:]

                imagecontent = requests.get(src)
                with open(workingDir + "/" + str(count) + filename, "wb") as outfile:
                    outfile.write(imagecontent.content)
                count += 1
            print("Done downloading files")

        except TimeoutException:
            print ("#")
            print ("#")
            print ("#")
            print ("#")            
            print ("#")
            print ("#") 
            print ("#")
            print ("#") 
            print ("Loading took too much time!")
            print ("#")
            print ("#")
            print ("#")
            print ("#")
            print ("#")
            print ("#")
            print ("#")
            print ("#")     




for inputlink in inputlinks:
    print("scraping(" + inputlink + ")")
    scrape(inputlink)
    driver.close()
    driver.quit()
    driver = webdriver.Chrome(options=options)



driver.close()
driver.quit()