from stellar_sdk import Asset, Keypair, Network, Server, TransactionBuilder, LiquidityPoolAsset
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import selenium.webdriver as webdriver
from datetime import datetime
from decimal import Decimal
from pprint import pprint
import requests, json, time, sys, sep10, cancelAllOustandingOffers

####### SET SPREAD, FEES, & SIZE #######
MIN_MEANINGFUL_SIZE = 500
TXN_FEE_STROOPS = 4269
MAX_BID = .99993
MIN_OFFER = 1.00007
MIN_BUY_SIDE_BID_SUPPORT = .995
MIN_BUY_SIDE_BID_LIQ = 50000
MIN_LIQ_PRICE = ".999"
MAX_LIQ_PRICE = "1.001"

BT_TREASURY = "GD2OUJ4QKAPESM2NVGREBZTLFJYMLPCGSUHZVRMTQMF5T34UODVHPRCY"
yUSDC_ISSUER = "GDGTVWSM4MGS4T7Z6W4RPWOCHE2I6RDFCIFZGS3DOA63LWQTRNZNTTFF"
USDC_ISSUER = "GA5ZSEJYB37JRC5AVCIA5MOP4RHTM335X2KGX3IHOJAPP5RE34K4KZVN"
LIQ_POOL_ID = "a92f55a5607db30047635970af435e4332ebbaff8a7fa70a9158c2fd6c1ecd2b"
TRANSFER_SERVER = sep10.transferServerSEP24("yUSDC", yUSDC_ISSUER).get()
HORIZON_INST = "horizon.stellar.org"
MAX_SEARCH = "200"
MIN_INCREMENT = Decimal(".0000001")
SLEEP_TIME = 12
LIQ_POOL_FEE = 30
MAX_OFFER = 99999
MIN_BID = 0.0000001
USDC_ASSET = Asset("USDC", USDC_ISSUER)
yUSDC_ASSET = Asset("yUSDC", yUSDC_ISSUER)
LIQ_POOL_ASSET = LiquidityPoolAsset(USDC_ASSET, yUSDC_ASSET, fee=LIQ_POOL_FEE)
PATH = Service(executable_path="/usr/bin/chromedriver")
DRIVER = webdriver.Chrome(service = PATH)
SERVER = Server(horizon_url = "https://" + HORIZON_INST)
TREASURY_ACCOUNT = SERVER.load_account(account_id = BT_TREASURY)
try:
    SECRET = sys.argv[1]
except Exception:
  SECRET = "SBTPLXTXJDMJOXFPYU2ANLZI2ARDPHFKPKK4MJFYVZVBLXYM5AIP3LPK"
  print("\n\n***Running without key (argv[1])***\n\n")
SIGNING_KEYPAIR = Keypair.from_secret(SECRET)
print("Starting yUSDC-USDC market making algorithm from {:.1f}bps spread".format(10000*(MIN_OFFER-MAX_BID)))

def main():
  myBid = USDCbuyOutstanding = USDCavailable = USDCtotal = yUSDCsellOutstanding = yUSDCavailable = yUSDCtotal = lastTime = liqPoolPos = Decimal(0)
  myAsk = Decimal(100)
  depositsFrozenFlag = withdrawsFrozenFlag = False
  token = sep10.Sep10("yUSDC", yUSDC_ISSUER, SECRET).run_auth()
  timeInAnHourToResetSEP24flagsPlusAuth = time.time() + 3600
  while(time.time() < timeInAnHourToResetSEP24flagsPlusAuth):
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
      except Exception:
        try:
          if(balances["liquidity_pool_id"] == LIQ_POOL_ID):
            liqPoolPos = Decimal(balances["balance"])
        except Exception:
          continue
    dollarsTotal = USDCtotal + yUSDCtotal
    requestAddress = data["_links"]["offers"]["href"].replace("{?cursor,limit,order}", "?limit={}".format(MAX_SEARCH))
    data = requests.get(requestAddress).json()
    outstandingOffers = data["_embedded"]["records"]
    for offers in outstandingOffers:
      if(offers["selling"]["asset_code"] == "yUSDC" and offers["buying"]["asset_code"] == "USDC"):
        myAsk = Decimal(offers["price"])
        myAskID = int(offers['id'])
      elif(offers["selling"]["asset_code"] == "USDC" and offers["buying"]["asset_code"] == "yUSDC"):
        myBid = Decimal(offers["price_r"]["d"]) / Decimal(offers["price_r"]["n"])
        myBidID = int(offers['id'])
    requestAddress = "https://" + HORIZON_INST + "/order_book?selling_asset_type=credit_alphanum12&selling_asset_code=yUSDC&selling_asset_issuer=" + yUSDC_ISSUER + "&buying_asset_type=credit_alphanum4&buying_asset_code=USDC&buying_asset_issuer=" + USDC_ISSUER + "&limit=" + MAX_SEARCH    
    data = requests.get(requestAddress).json()
    bidsFromStellar = data["bids"]
    asksFromStellar = data["asks"]
    highestMeaningfulCompetingBid = MIN_BID
    lowestMeaningfulCompetingOffer = MAX_OFFER
    buySideLiq = 0
    for bids in bidsFromStellar:
      amount = Decimal(bids["amount"])
      price = Decimal(bids["price"])
      if(amount < MIN_MEANINGFUL_SIZE or price == myBid):
        continue
      if(price > highestMeaningfulCompetingBid):
        highestMeaningfulCompetingBid = price
      if(price > MIN_BUY_SIDE_BID_SUPPORT):
        buySideLiq += amount
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
    matched = buyersTooExcited and sellersTooExcited
    tooHighBid = highestMeaningfulCompetingBid < myBid - MIN_INCREMENT
    tooLowAsk = lowestMeaningfulCompetingOffer > myAsk + MIN_INCREMENT
    meaningfullyOutbid = highestMeaningfulCompetingBid > myBid and USDCmeaningful
    meaningfullyUndercut = lowestMeaningfulCompetingOffer < myAsk and yUSDCmeaningful
    timeToBuy = meaningfullyOutbid or tooHighBid or notBuyingAll
    timeToSell = meaningfullyUndercut or tooLowAsk or notSellingAll
    enoughBuyers = buySideLiq > MIN_BUY_SIDE_BID_LIQ
    if(matched):
      cancelAllOustandingOffers.main()
      USDCtooMuch = USDCtotal > Decimal("1.2")*yUSDCtotal
      yUSDCtooMuch = yUSDCtotal > Decimal("1.2")*USDCtotal
      swapNeeded = USDCtooMuch or yUSDCtooMuch
      sufficientSize = notBuyingAll and notSellingAll
      if(swapNeeded and sufficientSize):
        transaction = buildTxnEnv()
        if(USDCtooMuch):
          appendSEP24buyOpToTxnEnvelope(transaction, 0, USDCtotal/Decimal("2"), token)
        else:
          appendSEP24sellOpToTxnEnvelope(transaction, 0, yUSDCtotal/Decimal("2"), token)
        submitUnbuiltTxnToStellar(transaction)
        time.sleep(320)
      elif(dollarsTotal > MIN_MEANINGFUL_SIZE):
        transaction = buildTxnEnv()
        transaction.append_liquidity_pool_deposit_op(
          liquidity_pool_id = LIQ_POOL_ID,
          max_amount_a = USDCtotal,
          max_amount_b = yUSDCtotal,
          min_price = MIN_LIQ_PRICE,
          max_price = MAX_LIQ_PRICE,
        )
        submitUnbuiltTxnToStellar(transaction)
        print("{} @ {}: Executed deposit to liquidity pool".format(datetime.now(), dollarsTotal))
    else:
      if(liqPoolPos):
        transaction = buildTxnEnv()
        transaction.append_liquidity_pool_withdraw_op(
          liquidity_pool_id = LIQ_POOL_ID,
          amount = liqPoolPos,
          min_amount_a = liqPoolPos,
          min_amount_b = liqPoolPos,
        )
        submitUnbuiltTxnToStellar(transaction)
        print("{} @ Nil: Executed withdraw from liquidity pool".format(datetime.now()))
        time.sleep(SLEEP_TIME)
        continue
      if(timeToBuy and enoughBuyers):
        transaction = buildTxnEnv()
        if(not depositsFrozenFlag and buyersTooExcited):
          lastTime = preventSEP24collisions(lastTime)
          frozen = appendSEP24buyOpToTxnEnvelope(transaction, myBidID, USDCtotal, token)
          if(frozen):
            depositsFrozenFlag = True
            continue
          submitUnbuiltTxnToStellar(transaction)
          print("{} @ {}: Executed SEP24 buy".format(datetime.now(), dollarsTotal))
        elif(not buyersTooExcited):
          bid = highestMeaningfulCompetingBid + MIN_INCREMENT
          transaction.append_manage_buy_offer_op(
            selling = USDC_ASSET,
            buying = yUSDC_ASSET,
            amount = USDCtotal,
            price = bid,
            offer_id = myBidID,
          )
          submitUnbuiltTxnToStellar(transaction)
          print("{} @ {}: Updated bid to {}".format(datetime.now(), dollarsTotal, bid))
      if(timeToSell):
        transaction = buildTxnEnv()
        if(not withdrawsFrozenFlag and sellersTooExcited):
          lastTime = preventSEP24collisions(lastTime)
          frozen = appendSEP24sellOpToTxnEnvelope(transaction, myAskID, yUSDCtotal, token)
          if(frozen):
            withdrawsFrozenFlag = True
            continue
          submitUnbuiltTxnToStellar(transaction)
          print("{} @ {}: Executed SEP24 sell".format(datetime.now(), dollarsTotal))
        elif(not sellersTooExcited):
          ask = lowestMeaningfulCompetingOffer - MIN_INCREMENT
          transaction.append_manage_sell_offer_op(
            selling = yUSDC_ASSET,
            buying = USDC_ASSET,
            amount = yUSDCtotal,
            price = ask,
            offer_id = myAskID,
          )
          submitUnbuiltTxnToStellar(transaction)
          print("{} @ {}: Updated ask to {}".format(datetime.now(), dollarsTotal, ask))
    time.sleep(SLEEP_TIME)
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
    return time.sleep(SLEEP_TIME)
  except Exception:
    return 0

def preventSEP24collisions(lastTime):
  if(lastTime > time.time() - 64):
    time.sleep(64 - SLEEP_TIME)
  return time.time()

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
  except Exception:
    print("{}: Attempted SEP24 deposit: disabled [{}]".format(datetime.now()))
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
    transactionEnvelope.append_manage_sell_offer_op(
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
  except Exception:
    print("{}: Attempted SEP24 withdraw: disabled [{}]".format(datetime.now()))
    return 1
  amountField = DRIVER.find_element(by=By.NAME, value="amount")
  amountField.send_keys(int(yUSDCtotal))
  networkField = DRIVER.find_element(by=By.NAME, value="to_address")
  networkField.send_keys(BT_TREASURY)
  DRIVER.find_element(by=By.CLASS_NAME, value="mdc-button__label").click()
  SEP24verifDepAddr = DRIVER.find_element(by=By.NAME, value="to_address").get_attribute("value")
  assert(SEP24verifDepAddr == BT_TREASURY)
  DRIVER.find_element(by=By.CLASS_NAME, value="mdc-button__label").click()
  SEP24destination = DRIVER.find_element(by=By.NAME, value="usdc_withdraw_wallet").get_attribute("value")
  SEP24amount = DRIVER.find_element(by=By.NAME, value="amount_to_deposit").get_attribute("value")
  SEP24memo = DRIVER.find_element(by=By.NAME, value="withdraw_memo").get_attribute("value")
  if(myAskID):
    transactionEnvelope.append_manage_sell_offer_op(
      selling = yUSDC_ASSET,
      buying = USDC_ASSET,
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

def redundant():
  while(True):
    try:
      main()
    except Exception:
      time.sleep(120)
      main()

redundant()