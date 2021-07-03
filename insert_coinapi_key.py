import time

import pyperclip
from selenium import webdriver

from lib import repository

while True:
    driver = webdriver.Chrome(
        executable_path=r"/mnt/c/Users/esfgs/selenium/chromedriver.exe")
    driver.maximize_window()

    driver.get("https://temp-mail.org/en/")
    while True:
        time.sleep(5)
        try:
            driver.find_element_by_xpath(
                "/html/body/div[1]/div/div/div[2]/div[1]/form/div[2]/button").click()
            email = pyperclip.paste()
            if "@" in email:
                break
        except Exception:
            pass

    driver.get("https://docs.coinapi.io/#md-docs")
    driver.find_element_by_xpath(
        "/html/body/header/div[2]/form/input").send_keys(email)
    driver.find_element_by_xpath('//*[@id="getFreeAPIKey"]').submit()
    while True:
        style = driver.find_element_by_xpath(
            '//*[@id="getFreeAPIKeyMessage"]').get_attribute("style")
        if style == "display: block;":
            break
        time.sleep(1)

    text = None
    while True:
        driver.get("https://temp-mail.org/en/")
        time.sleep(5)
        try:
            text = driver.find_element_by_xpath(
                "/html/body/main/div[1]/div/div[2]/div[2]/div/div[1]/div/div[4]/ul/li[2]/div[2]/span/a").click()
            break
        except Exception:
            pass

    text = None
    while True:
        try:
            text = driver.find_element_by_xpath(
                "/html/body/main/div[1]/div/div[2]/div[2]/div/div[1]/div/div[2]/div[3]/p[2]").text
            break
        except Exception:
            pass

    database = "tradingbot"
    key = text.split(" ")[2][:36]
    sql = f"insert into coinapi_key values ('{key}')"
    repository.execute(database=database, sql=sql)

    driver.close()
