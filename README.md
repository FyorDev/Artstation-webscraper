# Artstation-webscraper  
Use this to download all images from one or multiple links of an artist  

Needs selenium chrome, or replace with your own selenium browser.  

Put (multiple) artist links in links.txt and run artstationDownloader.py  
Or run artstationDownloader.py with an artist link as argument  
Or run linkGenerator.py with your account/following as the link to fill links.txt with everyone you follow and then run artstationDownloader.py  

Selenium is not run in headless mode since the javascript that loads the images doesn't seem to run then.

KNOWN ISSUE: sometimes Selenium freezes or crashes, just stop the program, delete the last updated incomplete artist folder and run again.

Related project: https://github.com/FyorUU/PureRef-format
