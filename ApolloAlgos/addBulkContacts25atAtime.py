from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import selenium.webdriver as webdriver
from pprint import pprint
import time

# from selenium.webdriver.chrome.options import Options
# 
# chrome_options = Options()
# #chrome_options.add_argument('--no-sandbox')
# chrome_options.add_argument('--headless')
# chrome_options.add_argument('--disable-gpu')
# chrome_options.add_argument('--disable-dev-shm-usage')
# chrome_options.add_argument('--start-maximized')
# chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
# chrome_options.add_experimental_option('useAutomationExtension', False)
# d = webdriver.Chrome("/usr/bin/chromedriver",chrome_options=chrome_options)
# d.get('https://www.google.nl/')

from pyvirtualdisplay import Display
display = Display(visible=0, size=(800, 800))  
display.start()

PATH = Service(executable_path="/usr/bin/chromedriver")
DRIVER = webdriver.Chrome(service = PATH)

## SETUP ##
# webpage = "https://app.apollo.io/#/people?finderViewId=62938ef1ce820a00a5cabc2b&personTitles[]=cfo&personLocations[]=United%20States&organizationLocations[]=United%20States&organizationTradingStatus[]=public&page=1&organizationNumEmployeesRanges[]=5001%2C10000&organizationNumEmployeesRanges[]=10001"
# webpage =  "https://app.apollo.io/#/people?finderViewId=62938ef1ce820a00a5cabc2b&personTitles[]=cfo&organizationNumEmployeesRanges[]=2001%2C5000&organizationNumEmployeesRanges[]=1001%2C2000&organizationNumEmployeesRanges[]=501%2C1000&organizationNumEmployeesRanges[]=201%2C500&organizationNumEmployeesRanges[]=101%2C200&organizationNumEmployeesRanges[]=51%2C100&organizationNumEmployeesRanges[]=21%2C50&organizationNumEmployeesRanges[]=11%2C20&personLocations[]=United%20States&organizationLocations[]=United%20States&organizationTradingStatus[]=public"
# webpage = "https://app.apollo.io/#/people?finderViewId=62938ef1ce820a00a5cabc2b&personTitles[]=cfo&organizationNumEmployeesRanges[]=2001%2C5000&organizationNumEmployeesRanges[]=1001%2C2000&organizationNumEmployeesRanges[]=501%2C1000&organizationNumEmployeesRanges[]=201%2C500&organizationNumEmployeesRanges[]=101%2C200&organizationNumEmployeesRanges[]=51%2C100&organizationTradingStatus[]=public&page=1&organizationLocations[]=United%20States"
webpage = "https://app.apollo.io/#/people?finderViewId=62938ef1ce820a00a5cabc2b&personTitles[]=cfo&organizationNumEmployeesRanges[]=2001%2C5000&organizationNumEmployeesRanges[]=1001%2C2000&organizationNumEmployeesRanges[]=501%2C1000&organizationNumEmployeesRanges[]=201%2C500&organizationNumEmployeesRanges[]=101%2C200&organizationNumEmployeesRanges[]=51%2C100&organizationTradingStatus[]=public&page=1&prospectedByCurrentTeam[]=no"
DRIVER.get("https://app.apollo.io")
time.sleep(1)
email = DRIVER.find_element(by=By.NAME, value="email")
email.send_keys("john@blocktransfer.io")
psswd = DRIVER.find_element(by=By.NAME, value="password")
psswd.send_keys("ESCqLZJ3j8?x/#f")
DRIVER.find_element(by=By.CLASS_NAME, value="zp_18q8k").click()
time.sleep(1)

def main():
  while(True):
    DRIVER.get(webpage)
    time.sleep(1)
    DRIVER.find_element(by=By.PARTIAL_LINK_TEXT, value="Net New").click()
    time.sleep(2)
    DRIVER.find_element(by=By.CLASS_NAME, value="zp_3Lc6D").click()
    DRIVER.find_element(by=By.PARTIAL_LINK_TEXT, value="Select this page").click()
    DRIVER.find_element(by=By.XPATH, value="//*[@class='zp-icon apollo-icon apollo-icon-plus zp_2BRav zp_35LDu zp_HPp4_']").click()
    actions = ActionChains(DRIVER);
    actions.send_keys("International Small-Cap Public American CFOs").perform()
    DRIVER.find_element(by=By.XPATH, value="//*[@class='zp-button zp_1TrB3']").click()
    print(f"25 contacts added")
    time.sleep(2)

def redundant():
  while(True):
    try:
      main()
    except Exception:
      time.sleep(1)

redundant()