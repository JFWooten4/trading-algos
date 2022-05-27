from stellar_sdk import Asset, Keypair, Network, Server, TransactionBuilder
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import selenium.webdriver as webdriver
from decimal import Decimal
from pprint import pprint
import requests, json, time, sys, sep10

BT_TREASURY = "GD2OUJ4QKAPESM2NVGREBZTLFJYMLPCGSUHZVRMTQMF5T34UODVHPRCY"
yUSDC_ISSUER = "GDGTVWSM4MGS4T7Z6W4RPWOCHE2I6RDFCIFZGS3DOA63LWQTRNZNTTFF"
USDC_ISSUER = "GA5ZSEJYB37JRC5AVCIA5MOP4RHTM335X2KGX3IHOJAPP5RE34K4KZVN"

TRANSFER_SERVER = sep10.getTransferServerSEP24("yUSDC", yUSDC_ISSUER).pullFromWeb()
HORIZON_INST = "horizon.stellar.org"
MAX_SEARCH = "200"
TXN_FEE_STROOPS = 4269

MIN_MEANINGFUL_SIZE = 500
MIN_INCREMENT = Decimal(".0000001")
MIN_BID = 0.0000001
MAX_BID = .99993
MIN_OFFER = 1.00007
MAX_OFFER = 99999

yUSDC_ASSET = Asset("yUSDC", yUSDC_ISSUER)
USDC_ASSET = Asset("USDC", USDC_ISSUER)

PATH = Service(executable_path="/usr/bin/chromedriver")
DRIVER = webdriver.Chrome(service = PATH)
SERVER = Server(horizon_url = "https://" + HORIZON_INST)
TREASURY_ACCOUNT = SERVER.load_account(account_id = BT_TREASURY)

def main():
  myBid = USDCbuyOutstanding = USDCavailable = USDCtotal = yUSDCsellOutstanding = yUSDCavailable = yUSDCtotal = Decimal(0)
  myAsk = Decimal(100)
  depositsFrozenFlag = withdrawsFrozenFlag = False
  try:
    SECRET = sys.argv[1]
  except:
    SECRET = "SBTPLXTXJDMJOXFPYU2ANLZI2ARDPHFKPKK4MJFYVZVBLXYM5AIP3LPK"
    print("Running without key. Usage: python3 mm-yUSDC-USDC.py $secret")
  signing_keypair = Keypair.from_secret(SECRET)
  webauth = sep10.Sep10("yUSDC", yUSDC_ISSUER, SECRET)
  token = webauth.run_auth()
  timeInAnHourToResetSEP24flagsPlusAuth = time.time() + 3600
  print("Starting yUSDC-USDC market making algorithm from {:.1f}bps spread".format(10000*(MIN_OFFER-MAX_BID)))
  while(time.time() < timeInAnHourToResetSEP24flagsPlusAuth):
    try:
      myBidID = myAskID = 0
      requestAddress = "https://" + HORIZON_INST + "/accounts/" + BT_TREASURY
      data = requests.get(requestAddress).json()
      accountBalances = data["balances"]
      for balances in accountBalances:
        try:
          if(balances["asset_code"] == "USDC"):
            USDCbuyOutstanding = Decimal(balances["selling_liabilities"])
            USDCtotal = Decimal(balances["balance"])
            USDCavailable = USDCtotal - USDCbuyOutstanding
          elif(balances["asset_code"] == "yUSDC"):
            yUSDCsellOutstanding = Decimal(balances["selling_liabilities"])
            yUSDCtotal = Decimal(balances["balance"])
            yUSDCavailable = yUSDCtotal - yUSDCsellOutstanding
        except:
          continue
      requestAddress = data["_links"]["offers"]["href"].replace("{?cursor,limit,order}", "?limit={}".format(MAX_SEARCH))
      data = requests.get(requestAddress).json()
      outstandingOffers = data["_embedded"]["records"]
      for offers in outstandingOffers:
        try:
          if(offers["selling"]["asset_code"] == "yUSDC" and offers["buying"]["asset_code"] == "USDC"):
            myAsk = Decimal(offers["price"])
            myAskID = int(offers['id'])
          elif(offers["selling"]["asset_code"] == "USDC" and offers["buying"]["asset_code"] == "yUSDC"):
            myBid = Decimal(offers["price_r"]["d"]) / Decimal(offers["price_r"]["n"]) # Always buying in terms of selling
            myBidID = int(offers['id'])
        except:
          continue
      requestAddress = "https://" + HORIZON_INST + "/order_book?selling_asset_type=credit_alphanum12&selling_asset_code=yUSDC&selling_asset_issuer=" + yUSDC_ISSUER + "&buying_asset_type=credit_alphanum4&buying_asset_code=USDC&buying_asset_issuer=" + USDC_ISSUER + "&limit=" + MAX_SEARCH    
      data = requests.get(requestAddress).json()
      bidsFromStellar = data["bids"]
      asksFromStellar = data["asks"]
      highestMeaningfulCompetingBid = MIN_BID
      lowestMeaningfulCompetingOffer = MAX_OFFER
      for bids in bidsFromStellar:
        if(Decimal(bids["amount"]) > MIN_MEANINGFUL_SIZE and Decimal(bids["price"]) > highestMeaningfulCompetingBid and highestMeaningfulCompetingBid != myBid):
          highestMeaningfulCompetingBid = Decimal(bids["price"])
      for offers in asksFromStellar:
        if(Decimal(offers["amount"]) > MIN_MEANINGFUL_SIZE and Decimal(offers["price"]) < lowestMeaningfulCompetingOffer and lowestMeaningfulCompetingOffer != myAsk):
          lowestMeaningfulCompetingOffer = Decimal(offers["price"])
      
      
      
      
      
      tooHigh = highestMeaningfulCompetingBid < myBid - MIN_INCREMENT
      tooLow = lowestMeaningfulCompetingOffer > myAsk + MIN_INCREMENT
      outbid = highestMeaningfulCompetingBid > myBid and USDCtotal > MIN_MEANINGFUL_SIZE
      undercut = lowestMeaningfulCompetingOffer < myAsk and yUSDCtotal > MIN_MEANINGFUL_SIZE
      
      
      tempOnlyIfNoSEP6bid = highestMeaningfulCompetingBid < 1
      tempOnlyIfNoSEP6ask = lowestMeaningfulCompetingOffer > 1
      
      if 0:#(outbid and tempOnlyIfNoSEP6bid):
        transaction = buildTxnEnv()
        if(highestMeaningfulCompetingBid >= MAX_BID and USDCavailable > MIN_MEANINGFUL_SIZE):
          frozen = appendSEP24buyOpToTxnEnvelope(transaction, myBidID, USDCtotal, token)
          if(frozen):
            depositsFrozenFlag = True
            continue
          print("Executed SEP6 buy")
        else:
          bid = highestMeaningfulCompetingBid + MIN_INCREMENT
          transaction.append_manage_buy_offer_op(
            selling = USDC_ASSET,
            buying = yUSDC_ASSET,
            amount = USDCtotal,
            price = bid,
            offer_id = myBidID,
          )
          print("Updated bid to {}".format(bid))
        submitUnbuiltTxnToStellar(transaction, signing_keypair)
      
      if 2:#(undercut and tempOnlyIfNoSEP6ask):
        transaction = buildTxnEnv()
        if 2:#(lowestMeaningfulCompetingOffer <= MIN_OFFER and yUSDCavailable > MIN_MEANINGFUL_SIZE):
          frozen = appendSEP24sellOpToTxnEnvelope(transaction, myAskID, yUSDCtotal, token)
          if(frozen):
            withdrawsFrozenFlag = True
            continue
          print("Executed SEP6 sell")
          
          print(transaction.set_timeout(30).build().to_xdr())
          return 2 #     WITHDRAWLS NOT TESTED YET -- DO NOT PUT INTO PRODUCTION
        else:
          ask = lowestMeaningfulCompetingOffer - MIN_INCREMENT
          transaction.append_manage_sell_offer_op(
            selling = yUSDC_ASSET,
            buying = USDC_ASSET,
            amount = "{:.7f}".format(yUSDCtotal / ask),
            price = ask,
            offer_id = myAskID,
          )
          print("Updated ask to {}".format(ask))
        submitUnbuiltTxnToStellar(transaction, signing_keypair)
      time.sleep(10)
    except KeyboardInterrupt:#Exception:
      print("Failed exception")
      return 0
      continue
  main()

def buildTxnEnv():
  return(
    TransactionBuilder(
      source_account = TREASURY_ACCOUNT,
      network_passphrase = Network.PUBLIC_NETWORK_PASSPHRASE,
      base_fee = TXN_FEE_STROOPS,
    )
  )

def submitUnbuiltTxnToStellar(transaction, signing_keypair):
  try:
    transaction = transaction.set_timeout(30).build()
    transaction.sign(signing_keypair)
    SERVER.submit_transaction(transaction)
  except:
    return 0

def appendSEP24buyOpToTxnEnvelope(transactionEnvelope, myBidID, USDCtotal, token):
  ultrastellarServer = TRANSFER_SERVER + "/transactions/deposit/interactive"
  auth = { "Authorization": "Bearer " + token, }
  info = {
    "asset_code": "yUSDC",
    "account": BT_TREASURY,
    "email_address": "treasury@blocktransfer.io",
    "amount": int(USDCtotal),
    "account": BT_TREASURY,
  }
  response = requests.post(ultrastellarServer, headers=auth, data=info)
  try:
    DRIVER.get(response.json()["url"])
  except:
    print("Attempted SEP24 deposit: disabled")
    return 1
  networkField = DRIVER.find_element(by=By.NAME, value="network")
  networkField.send_keys("stellar")
  DRIVER.find_element(by=By.CLASS_NAME, value="mdc-button__label").click()
  SEP24destination = DRIVER.find_element(by=By.NAME, value="usdc_deposit_wallet").get_attribute("value")
  SEP24amount = DRIVER.find_element(by=By.NAME, value="amount_to_deposit").get_attribute("value")
  SEP24memo = DRIVER.find_element(by=By.NAME, value="xlm_deposit_wallet").get_attribute("value")
  if(myBidID):
    transactionEnvelope.append_manage_buy_offer_op(
      selling = USDC_ASSET,
      buying = yUSDC_ASSET,
      amount = "0",
      price = "1",
      offer_id = myBidID,
    )
  transactionEnvelope.append_payment_op(
    destination = SEP24destination,
    asset = USDC_ASSET,
    amount = SEP24amount,
  ).add_text_memo(SEP24memo)
  DRIVER.close()
  return 0

def appendSEP24sellOpToTxnEnvelope(transactionEnvelope, myAskID, yUSDCtotal, token):
  ultrastellarServer = TRANSFER_SERVER + "/transactions/withdraw/interactive"
  print(ultrastellarServer)
  auth = { "Authorization": "Bearer " + token, }
  info = {
    "asset_code": "yUSDC",
    "account": BT_TREASURY,
    "email_address": "treasury@blocktransfer.io",
    "amount": yUSDCtotal,
    "account": BT_TREASURY,
  }
  response = requests.post(ultrastellarServer, headers=auth, data=info)
  try:
    DRIVER.get(response.json()["url"])
  except:
    print("Attempted SEP24 withdraw: disabled")
    return 1
  networkField = DRIVER.find_element(by=By.NAME, value="network")
  networkField.send_keys("stellar")
  DRIVER.find_element(by=By.CLASS_NAME, value="mdc-button__label").click()
  SEP24destination = DRIVER.find_element(by=By.NAME, value="usdc_deposit_wallet").get_attribute("value")
  SEP24amount = DRIVER.find_element(by=By.NAME, value="amount_to_deposit").get_attribute("value")
  SEP24memo = DRIVER.find_element(by=By.NAME, value="xlm_deposit_wallet").get_attribute("value")
  if(myAskID):
    transactionEnvelope.append_manage_sell_offer_op(
      selling = USDC_ASSET,
      buying = yUSDC_ASSET,
      amount = "0",
      price = "1",
      offer_id = myAskID,
    )
  transactionEnvelope.append_payment_op(
    destination = SEP24destination,
    asset = yUSDC_ASSET,
    amount = SEP24amount,
  ).add_text_memo(SEP24memo)
  DRIVER.close()
  return 0

main()