# Python 3.10

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
import datetime
import re
import os
from wakepy import keep
import winsound

prompt = "Completely translate the below chapter into English, with no omissions. Surround the translated text with four ampersands at the top and four ampersands at the bottom. At the end, outside of those, append a bit indicating whether anything was omitted, and count the number of sentences in the original text vs. the translation."
raw_source_url = ""
chrome_data_store_location = ""
chrome_profile_directory = ""
raw_source_url=""
regex_to_remove_from_raw = ""
next_link_text = "下一章"
start_chapter = 1
max_chapter = 800


def chapter_ch(chapter_number):
    return "chapter_" + str(chapter_number) + "_CH.txt"

def chapter_abspath_ch(chapter_number):
    return os.path.abspath(chapter_ch(chapter_number))

def chapter_abspath_en(chapter_number):
    return os.path.abspath("chapter_" + str(chapter_number) + "_EN.txt")

def wait_for_element(by_method, search_string):
    timeout = 0
    while True:
        elements = driver.find_elements(by_method, search_string)
        if len(elements) > 0:
            return elements[0]
        timeout += 1
        if timeout > 1200:
            raise Exception("excessive time spent in translation")
        time.sleep(1)

def setup():
    global driver, main_window_handle
    
    #create chromeoptions instance
    options = webdriver.ChromeOptions()
    #options.add_argument("--headless")
    #options.add_argument("--no-sandbox")

    #provide location where chrome stores profiles
    options.add_argument("--user-data-dir=" + chrome_data_store_location)

    #provide the profile name with which we want to open browser
    options.add_argument(r'--profile-directory=' + chrome_profile_directory)

    #specify where your chrome driver present in your pc
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(40)
    main_window_handle = driver.current_window_handle
    assert main_window_handle is not None

def get_chapter(chapter_number):
    driver.get(raw_source_url)
    chapter_link = driver.find_element(By.PARTIAL_LINK_TEXT, '【'+str(chapter_number)+'】')
    chapter_link.click()
    chapter_text = ""
    while '【'+str(chapter_number)+'】' in driver.title:
        page_content = driver.find_element(By.ID, "chaptercontent")
        raw_text = page_content.text
        page_text = re.sub(regex_to_remove_from_raw, '', raw_text)
        chapter_text += page_text
        next_link = driver.find_element(By.LINK_TEXT, next_link_text)
        next_link.click()
    with open("chapter_" + str(chapter_number) + "_CH.txt", "w", encoding="utf-8") as text_file:
        text_file.write(chapter_text)
    print("Chapter text retrieved for chapter " + str(chapter_number))
    return chapter_text

def check_if_rate_limited():
    print("Checking if rate-limited.")
    driver.implicitly_wait(0)
    limit_objects = driver.find_elements(By.CSS_SELECTOR, 'div.text-regular')
    driver.implicitly_wait(40)
    if len(limit_objects) == 0 or not "You are out of free messages" in limit_objects[0].text:
        print("Not rate-limited.")
        return
    limit_text = limit_objects[0].text
    print(limit_text)
    am_pm = limit_text.split()[-1]
    target_hour = int(limit_text.split()[-2])
    if am_pm == "PM":
        target_hour += 12
    t = datetime.datetime.today()
    future = datetime.datetime(t.year,t.month,t.day,target_hour,0)
    if t.hour >= target_hour:
        future += datetime.timedelta(days=1)
    time_to_sleep = (future-t).total_seconds() + 61
    print("Sleeping for " + str(time_to_sleep) + " seconds.")
    time.sleep((future-t).total_seconds())
    driver.get("https://claude.ai/")
    time.sleep(3)
    driver.refresh()
    time.sleep(3)

def translate_text(chapter_number):
    #open Claude
    driver.get("https://claude.ai/")
    time.sleep(5)

    check_if_rate_limited()
 
    #find input box and upload file
    file_input = driver.find_element(By.CSS_SELECTOR, "input[type=file]")
    file_input.send_keys(chapter_abspath_ch(chapter_number))

    time.sleep(5)

    #find text box and add text
    search_box = driver.find_element(By.CSS_SELECTOR, 'p.is-empty')
    search_box.send_keys(prompt)

    # wait for upload to complete
    driver.find_element(By.CSS_SELECTOR, 'div[title="'+chapter_ch(chapter_number)+'"] > button[aria-label]')

    print("About to push the button to translate chapter " + str(chapter_number))
    time.sleep(5)

    #click the go button
    go_button = driver.find_element(By.CSS_SELECTOR, 'div[data-value="new chat"] > button')
    go_button.click()

    #confirm the translation is in progress
    time.sleep(3)
    driver.find_element(By.CSS_SELECTOR, 'div.place-self-start')

    # Wait until translation is done.
    print("Waiting for completion of chapter " + str(chapter_number))
    wait_for_element(By.XPATH, '//button[text()="Retry"]')

    # find the translated output
    print("Waiting for text for chapter " + str(chapter_number))
    text_object = wait_for_element(By.CSS_SELECTOR, 'div.place-self-start')
    text = text_object.text

    output_match = re.search('&&&&+([\s\S]+)&&&&+', text)
    if output_match and output_match.group(1):
        text = output_match.group(1)

    if text == None or len(text) < 10:
        if text == None:
            print("Error: Text is null.")
        else:
            print("Error: Text is " + text)
        print("Original, pre-trimming text was " + text_object.text)
        raise Exception("empty text")

    with open(chapter_abspath_en(chapter_number), "w", encoding="utf-8") as text_file:
        text_file.write(text)

second_try = False

with keep.running() as k:
    setup()

    chapter_num = start_chapter
    try_login = False

    while (chapter_num < max_chapter):
        # skip chapters we already have
        while os.path.exists(chapter_abspath_en(chapter_num)):
            chapter_num += 1
        try:
            get_chapter(chapter_num)
            translate_text(chapter_num)
        except Exception as e:
            print("Error translating chapter " + str(chapter_num) + ": " + str(e))
            time.sleep(10)
            frequency = 2000  # Set Frequency To 2500 Hertz
            duration = 500    # Set Duration To 1000 ms == 1 second
            winsound.Beep(frequency, duration)
            time.sleep(30)
            continue
        print("Finished chapter " + str(chapter_num))
        second_try = False
        chapter_num += 1
        time.sleep(20)
        continue
