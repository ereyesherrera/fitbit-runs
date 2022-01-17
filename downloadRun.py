from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
import time
import re
import os
import pyautogui

DOWNLOADS = '/Users/EdwinReyesHerrera/Downloads'
RUN_FOLDER = "/Users/EdwinReyesHerrera/Documents/Python_Projects/Fitbit Runs/Fitbit TCX Files"


def move_files(source_folder, target_folder, file_type):
    """
    Reads files of a specific extension and moves them to a different location on computer
    :param file_type: Extension of files to be moved
    :param source_folder: Folder where files are currently stored
    :param target_folder: Folder where files will be moved
    :return: Message to communicate successful run of function
    """
    for f_name in os.listdir(source_folder):
        if f_name.endswith(file_type):
            name = re.sub(file_type, '', f_name)
            os.rename(source_folder + '/' + name + file_type,
                      target_folder + '/' + name + file_type)
    return "Process Complete"


def download_run_links():
    """
    Logs into Fitbit account, loads all run/bike activities on page and saves links to text file
    :return: Message to communicate successful run of function
    """

    # Starting browser
    browser = webdriver.Chrome("/Users/EdwinReyesHerrera/Documents/Python_Projects/chromedriver")
    browser.get("https://www.fitbit.com/activities")

    # Allow page to fully load
    time.sleep(8)

    # Login Page
    email = browser.find_element_by_xpath('/html/body/div[2]/div/div[2]/div/div/div[3]/form/div[1]/div/input')
    password = browser.find_element_by_xpath('/html/body/div[2]/div/div[2]/div/div/div[3]/form/div[2]/div/input')
    login_button = browser.find_element_by_xpath('/html/body/div[2]/div/div[2]/div/div/div[3]/form/div[4]/div/button')
    remember_me = browser.find_element_by_xpath('/html/body/div[2]/div/div[2]/div/div/div[3]/form/div[3]/div[1]/input')

    # Prompt User to enter credentials
    email.send_keys(input("Enter email: "))
    password.send_keys(input("Enter password: "))
    remember_me.click()
    login_button.click()  # Login once credentials inputted

    time.sleep(8)

    # Loading Full Page of Activities
    # Only displays 10 at a time on one page, so need to automate loading more
    while True:
        try:
            time.sleep(4)
            load_more = browser.find_element_by_xpath("/html/body/div[7]/div/div/section[2]/div/div/form/button")
            load_more.click()
            browser.execute_script("window.scrollBy(0,500)", "")
        except NoSuchElementException:
            print("All Activities Loaded")
            break

    # Gets each row (i.e. activity) of table now displayed on the page
    activities = browser.find_elements_by_xpath('//*[@id="contentBody"]/section[2]/div/div/table/tbody')

    runs = []
    for i in activities:
        # Only save links to activities that are running/biking and that have GPS data
        if i.find_element_by_xpath('./tr[1]/td[2]').text in ['Run', 'Outdoor Bike', 'Bike', 'Walk'] \
                and i.find_element_by_xpath('./tr[1]/td[4]').text != 'N/A':
            runs.append(i.find_element_by_xpath('./tr[1]/td[7]/ul/li[1]/a').get_attribute('href'))

    # Save links to text file to access later and in waves
    with open('runLinks.txt', 'w') as runLinks:
        for link in runs:
            runLinks.write(link + '\n')

    browser.close()
    return "Process Complete"


def download_run_files():
    """
    Opens links to Fitbit Activities and downloads GPS data (as .tcx files) to folder
    Allows for downloading files in chunks, not all at once
    :return: Message to communicate successful run of function
    """
    with open('runLinks.txt', 'r') as runFile:
        runs = []
        # Only get IDs of each activity needing to be downloaded
        for i in runFile.readlines():
            runs.append(re.sub(re.sub('\\d+' + '\n', '', i), '', i).strip())

    # If function has run before, get IDs of all activities that have already been downloaded
    downloaded_files = []
    for f_name in os.listdir("/Users/EdwinReyesHerrera/Documents/Python_Projects/Fitbit Runs/Fitbit TCX Files"):
        if f_name.endswith('.tcx'):
            name = re.sub('.tcx', '', f_name)
            downloaded_files.append(name)

    # Open browser
    browser = webdriver.Chrome("/Users/EdwinReyesHerrera/Documents/Python_Projects/chromedriver")
    browser.get("https://www.fitbit.com/activities")

    time.sleep(8)

    # Login Page
    email = browser.find_element_by_xpath('/html/body/div[2]/div/div[2]/div/div/div[3]/form/div[1]/div/input')
    password = browser.find_element_by_xpath('/html/body/div[2]/div/div[2]/div/div/div[3]/form/div[2]/div/input')
    login_button = browser.find_element_by_xpath('/html/body/div[2]/div/div[2]/div/div/div[3]/form/div[4]/div/button')
    remember_me = browser.find_element_by_xpath('/html/body/div[2]/div/div[2]/div/div/div[3]/form/div[3]/div[1]/input')

    email.send_keys(input("Enter email: "))
    password.send_keys(input("Enter password: "))
    remember_me.click()
    login_button.click()

    time.sleep(8)

    for run in runs:
        # If function ran before, only visit links and download content for those that don't
        # exist in folder yet
        if run not in downloaded_files and run != '31434932767':
            # '31434932767' is ID of activity that doesn't load correctly
            browser.get('https://www.fitbit.com/activities/exercise/{}'.format(run))
            # Clicking and downloading drop down menu to view download options
            while True:
                try:
                    time.sleep(10)
                    options = browser.find_element_by_xpath('/html/body/div[5]/div[3]/div[1]/div/div[1]/div/div['
                                                            '3]/button')
                    options.click()
                except NoSuchElementException:
                    pass
                else:
                    # Clicking and downloading the tcx file that contains run data
                    try:
                        tcx_file = browser.find_element_by_xpath(
                            '/html/body/div[5]/div[3]/div[1]/div/div[2]/div/ul/li[1]/button')
                        tcx_file.click()
                        time.sleep(10)
                    except NoSuchElementException:
                        pass
                break
            # Keeping computer awake
            pyautogui.moveRel(0, 10)
            pyautogui.moveRel(0, -10)

        # Move files to correct folder once downloaded
        move_files(DOWNLOADS, RUN_FOLDER, '.tcx')

    return "Process Complete"


# download_run_links() # Only run once to get text file of links to all activities
download_run_files()  # Run as many times as needed to download all activities
