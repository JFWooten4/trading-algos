from stellar_sdk import Asset, Keypair, Network, Server, TransactionBuilder
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import selenium.webdriver as webdriver
from decimal import Decimal
from pprint import pprint
import requests, json, time, sys, sep10

####### SET SPREAD, FEES, & SIZE #######
MIN_MEANINGFUL_SIZE = 420.69
TXN_FEE_STROOPS = 4269
MAX_BID = .99993
MIN_OFFER = 1.00007

BT_TREASURY = "GD2OUJ4QKAPESM2NVGREBZTLFJYMLPCGSUHZVRMTQMF5T34UODVHPRCY"
yUSDC_ISSUER = "GDGTVWSM4MGS4T7Z6W4RPWOCHE2I6RDFCIFZGS3DOA63LWQTRNZNTTFF"
USDC_ISSUER = "GA5ZSEJYB37JRC5AVCIA5MOP4RHTM335X2KGX3IHOJAPP5RE34K4KZVN"
TRANSFER_SERVER = sep10.transferServerSEP24("yUSDC", yUSDC_ISSUER).get()
HORIZON_INST = "horizon.stellar.org"
MAX_SEARCH = "200"
MIN_INCREMENT = Decimal(".0000001")
MAX_OFFER = 99999
MIN_BID = 0.0000001
yUSDC_ASSET = Asset("yUSDC", yUSDC_ISSUER)
USDC_ASSET = Asset("USDC", USDC_ISSUER)
PATH = Service(executable_path="/usr/bin/chromedriver")
DRIVER = webdriver.Chrome(service = PATH)
SERVER = Server(horizon_url = "https://" + HORIZON_INST)
TREASURY_ACCOUNT = SERVER.load_account(account_id = BT_TREASURY)
try:
    SECRET = sys.argv[1]
except:
  SECRET = "SBTPLXTXJDMJOXFPYU2ANLZI2ARDPHFKPKK4MJFYVZVBLXYM5AIP3LPK"
  print("Running without key. Usage: python3 mm-yUSDC-USDC.py $secret")
SIGNING_KEYPAIR = Keypair.from_secret(SECRET)
print("Starting yUSDC-USDC market making algorithm from {:.1f}bps spread".format(10000*(MIN_OFFER-MAX_BID)))

def main():
  myBid = USDCbuyOutstanding = USDCavailable = USDCtotal = yUSDCsellOutstanding = yUSDCavailable = yUSDCtotal = Decimal(0)
  myAsk = Decimal(100)
  depositsFrozenFlag = withdrawsFrozenFlag = False
  token = sep10.Sep10("yUSDC", yUSDC_ISSUER, SECRET).run_auth()
  timeInAnHourToResetSEP24flagsPlusAuth = time.time() + 3600
  while(time.time() < timeInAnHourToResetSEP24flagsPlusAuth):
    try:
      myBidID = myAskID = 0
      requestAddress = "https://" + HORIZON_INST + "/accounts/" + BT_TREASURY
      data = requests.get(requestAddress).json()
      accountBalances = data["balances"]
    except Exception:
      pprint(data)
      continue
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
    try:    
      requestAddress = data["_links"]["offers"]["href"].replace("{?cursor,limit,order}", "?limit={}".format(MAX_SEARCH))
      data = requests.get(requestAddress).json()
      outstandingOffers = data["_embedded"]["records"]
    except Exception:
      pprint(data)
      continue
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
    try:
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
        if(Decimal(offers["amount"]) > MIN_MEANINGFUL_SIZE and Decimal(offers["price"]) < lowestMeaningfulCompetingOffer and Decimal(offers["price"]) != myAsk):
          lowestMeaningfulCompetingOffer = Decimal(offers["price"])
      ####### BEGIN TRADING LOGIC #######
      USDCmeaningful = USDCtotal > MIN_MEANINGFUL_SIZE
      yUSDCmeaningful = yUSDCtotal > MIN_MEANINGFUL_SIZE
      notBuyingAll = USDCavailable > MIN_MEANINGFUL_SIZE
      notSellingAll = yUSDCavailable > MIN_MEANINGFUL_SIZE
      buyersTooExcited = highestMeaningfulCompetingBid >= MAX_BID
      sellersTooExcited = lowestMeaningfulCompetingOffer <= MIN_OFFER
      tooHighBid = highestMeaningfulCompetingBid < myBid - MIN_INCREMENT
      tooLowAsk = lowestMeaningfulCompetingOffer > myAsk + MIN_INCREMENT
      meaningfullyOutbid = highestMeaningfulCompetingBid > myBid and USDCmeaningful
      meaningfullyUndercut = lowestMeaningfulCompetingOffer < myAsk and yUSDCmeaningful
      if(meaningfullyOutbid or tooHighBid or notBuyingAll):
        transaction = buildTxnEnv()
        if(not depositsFrozenFlag and buyersTooExcited):
          frozen = appendSEP24buyOpToTxnEnvelope(transaction, myBidID, USDCtotal, token)
          if(frozen):
            depositsFrozenFlag = True
            continue
          print("Executed SEP24 buy")
        elif(not buyersTooExcited):
          bid = highestMeaningfulCompetingBid + MIN_INCREMENT
          transaction.append_manage_buy_offer_op(
            selling = USDC_ASSET,
            buying = yUSDC_ASSET,
            amount = USDCtotal,
            price = bid,
            offer_id = myBidID,
          )
          print("Updated bid to {}".format(bid))
        submitUnbuiltTxnToStellar(transaction)
      if(meaningfullyUndercut or tooLowAsk or notSellingAll):
        transaction = buildTxnEnv()
        
        
        
        
        
        tempDisable = True
        if(not withdrawsFrozenFlag and sellersTooExcited and not tempDisable):
          frozen = appendSEP24sellOpToTxnEnvelope(transaction, myAskID, yUSDCtotal, token)
          if(frozen):
            withdrawsFrozenFlag = True
            continue
          print("Executed SEP24 sell")
          
          print(transaction.set_timeout(30).build().to_xdr())
          return 2 #     WITHDRAWLS NOT TESTED YET -- DO NOT PUT INTO PRODUCTION
          
        
        
        
        
        
        
        elif(not sellersTooExcited):
          ask = lowestMeaningfulCompetingOffer - MIN_INCREMENT
          transaction.append_manage_sell_offer_op(
            selling = yUSDC_ASSET,
            buying = USDC_ASSET,
            amount = yUSDCtotal, #"{:.7f}".format(yUSDCtotal), #TODO: Works? 
            price = ask,
            offer_id = myAskID,
          )
          print("Updated ask to {}".format(ask))
        submitUnbuiltTxnToStellar(transaction)
    except Exception:
      continue
    time.sleep(10)
  main()

def buildTxnEnv():
  return(
    TransactionBuilder(
      source_account = TREASURY_ACCOUNT,
      network_passphrase = Network.PUBLIC_NETWORK_PASSPHRASE,
      base_fee = TXN_FEE_STROOPS,
    )
  )

def submitUnbuiltTxnToStellar(transaction):
  try:
    transaction = transaction.set_timeout(30).build()
    transaction.sign(SIGNING_KEYPAIR)
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
    "account": BT_TREASURY,
  }
  response = requests.post(ultrastellarServer, headers=auth, data=info)
  try:
    DRIVER.get(response.json()["url"])
  except:
    print("Attempted SEP24 deposit: disabled")
    return 1
  amountField = DRIVER.find_element(by=By.NAME, value="amount")
  amountField.send_keys(int(USDCtotal))
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
  return 0

def appendSEP24sellOpToTxnEnvelope(transactionEnvelope, myAskID, yUSDCtotal, token):
  ultrastellarServer = TRANSFER_SERVER + "/transactions/withdraw/interactive"
  print(ultrastellarServer)
  auth = { "Authorization": "Bearer " + token, }
  info = {
    "asset_code": "yUSDC",
    "account": BT_TREASURY,
    "email_address": "treasury@blocktransfer.io",
    "account": BT_TREASURY,
  }
  response = requests.post(ultrastellarServer, headers=auth, data=info)
  try:
    DRIVER.get(response.json()["url"])
  except:
    print("Attempted SEP24 withdraw: disabled")
    return 1
  amountField = DRIVER.find_element(by=By.NAME, value="amount")
  amountField.send_keys(yUSDCtotal)
  networkField = DRIVER.find_element(by=By.NAME, value="network")
  networkField.send_keys("stellar")
  print("Test: Sleeping: verify amount field")
  time.sleep(100)
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
  return 0

main()