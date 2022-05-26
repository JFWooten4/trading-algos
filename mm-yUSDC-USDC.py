from stellar_sdk import Asset, Keypair, Network, Server, TransactionBuilder
#from webdriver_manager.chrome import ChromeDriverManager
from decimal import Decimal, getcontext
import requests, json, time, sys, sep10
#from selenium import webdriver 
from pprint import pprint

BT_TREASURY = "GD2OUJ4QKAPESM2NVGREBZTLFJYMLPCGSUHZVRMTQMF5T34UODVHPRCY"
yUSDC_ISSUER = "GDGTVWSM4MGS4T7Z6W4RPWOCHE2I6RDFCIFZGS3DOA63LWQTRNZNTTFF"
USDC_ISSUER = "GA5ZSEJYB37JRC5AVCIA5MOP4RHTM335X2KGX3IHOJAPP5RE34K4KZVN"

TRANSFER_SERVER = "https:// ... ultrastellar.com/sep24" # just make this right ... (could programatically fetch?)
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
#driver = webdriver.Chrome(executable_path=os.path.abspath("chromedriver.exe"))
#driver = webdriver.Chrome(ChromeDriverManager().install())
SERVER = Server(horizon_url = "https://" + HORIZON_INST)
TREASURY_ACCOUNT = SERVER.load_account(account_id = BT_TREASURY)

def main():
  #getcontext().prec = 7
  myBid = USDCbuyOutstanding = USDCavailable = USDCtotal = yUSDCsellOutstanding = yUSDCavailable = yUSDCtotal = Decimal(0)
  myAsk = Decimal(100)
  try:
    SECRET = sys.argv[1]
  except:
    SECRET = "SBTPLXTXJDMJOXFPYU2ANLZI2ARDPHFKPKK4MJFYVZVBLXYM5AIP3LPK"
    print("Running without key. Usage: python3 mm-yUSDC-USDC.py $secret")
  signing_keypair = Keypair.from_secret(SECRET)
  webauth = sep10.Sep10("yUSDC", yUSDC_ISSUER, SECRET)
  token = webauth.run_auth() # Expires in a day
  timeIn23hours = time.time() + 86400
  
  print("Starting yUSDC-USDC market making algorithm from {:.1f}bps spread".format(10000*(MIN_OFFER-MAX_BID)))
  while(time.time() < timeIn23hours):
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
    for bids in bidsFromStellar:
      if(Decimal(bids["amount"]) > MIN_MEANINGFUL_SIZE and Decimal(bids["price"]) > highestMeaningfulCompetingBid and highestMeaningfulCompetingBid != myBid):
        highestMeaningfulCompetingBid = Decimal(bids["price"])
    
    lowestMeaningfulCompetingOffer = MAX_OFFER
    for offers in asksFromStellar:
      if(Decimal(offers["amount"]) > MIN_MEANINGFUL_SIZE and Decimal(offers["price"]) < lowestMeaningfulCompetingOffer and lowestMeaningfulCompetingOffer != myAsk):
        lowestMeaningfulCompetingOffer = Decimal(offers["price"])

    # BEGIN TRADING LOGIC #
    
    # These could be useful if many people mess with the algo with flash bids...
    # tooHigh = lowestMeaningfulCompetingBid < myBid - MIN_INCREMENT
    # tooLow = lowestMeaningfulCompetingOffer > myAsk + MIN_INCREMENT
    
    tempOnlyIfNoSEP6bid = highestMeaningfulCompetingBid < 1
    tempOnlyIfNoSEP6ask = lowestMeaningfulCompetingOffer > 1
    
    if(highestMeaningfulCompetingBid > myBid and USDCtotal > 5 and tempOnlyIfNoSEP6bid):
      transaction = TransactionBuilder(
        source_account = TREASURY_ACCOUNT,
        network_passphrase = Network.PUBLIC_NETWORK_PASSPHRASE,
        base_fee = TXN_FEE_STROOPS,
      )
      #if(highestMeaningfulCompetingBid >= MAX_BID and USDCavailable > MIN_MEANINGFUL_SIZE):
      #  appendSEP6buyOpToTxnEnvelope(transaction, myBidID, USDCtotal)
      #else:
      bid = highestMeaningfulCompetingBid + MIN_INCREMENT
      transaction.append_manage_buy_offer_op(
        selling = USDC_ASSET,
        buying = yUSDC_ASSET,
        amount = USDCtotal,
        price = bid,
        offer_id = myBidID,
      )
      if(submitUnbuiltTxnToStellar(transaction, signing_keypair)):
        print("Updated bid to {}".format(bid))
    
    if(lowestMeaningfulCompetingOffer < myAsk and yUSDCtotal > 5 and tempOnlyIfNoSEP6ask):
      transaction = TransactionBuilder(
        source_account = TREASURY_ACCOUNT,
        network_passphrase = Network.PUBLIC_NETWORK_PASSPHRASE,
        base_fee = TXN_FEE_STROOPS,
      )
      #if(lowestMeaningfulCompetingOffer <= MIN_OFFER and yUSDCavailable > MIN_MEANINGFUL_SIZE):
      #  appendSEP6sellOpToTxnEnvelope(transaction, myAskID, yUSDCtotal)
      #else:
      ask = lowestMeaningfulCompetingOffer - MIN_INCREMENT
      transaction.append_manage_sell_offer_op(
        selling = yUSDC_ASSET,
        buying = USDC_ASSET,
        amount = "{:.7f}".format(yUSDCtotal / ask),
        price = ask,
        offer_id = myAskID,
      )
      if(submitUnbuiltTxnToStellar(transaction, signing_keypair)):
        print("Updated ask to {}".format(ask))
    time.sleep(10)
  main()

def submitUnbuiltTxnToStellar(transaction, signing_keypair):
  try:
    transaction = transaction.set_timeout(30).build()
    transaction.sign(signing_keypair)
    SERVER.submit_transaction(transaction)
    return 420
  except:
    return 0

# testing debug with buy side 
def appendSEP6buyOpToTxnEnvelope(transactionEnvelope, myBidID, USDCtotal):
  print("Tries to do a SEP-6 buy")
  # cancel outstaning buy offer (then use total USDC)
  if(myBidID):
    transactionEnvelope.append_manage_buy_offer_op(
      selling = USDC_ASSET,
      buying = yUSDC_ASSET,
      amount = 0,
      price = 1,
      offer_id = myBidID,
    )
  
  ultrastellarServer = "https://" + TRANSFER_SERVER + "/transactions/deposit/interactive"
  print(token)
  print(ultrastellarServer)
  reqAddr = ultrastellarServer# + "?asset_code=yUSDC&account=" + BT_TREASURY
  print(reqAddr)
  auth = {
    "Authorization": "Bearer " + token,
  }
  info = {
    "asset_code": "yUSDC",
    "account": BT_TREASURY,
    "email_address": "treasury@blocktransfer.io",
    "amount": int(USDCtotal),
    "account": BT_TREASURY,
    "id_network": "stellar",
  }
  response = requests.post(reqAddr, headers = auth, data = info)
  print("WIN")
  # parse response.json()["how"]
  pprint(response)
  pprint(response.json())
  url = response.json()["url"]
  driver.get(url)
  return 1
  transactionEnvelope.append_payment_op( #
    destination = 1, # 
    asset = USDC_ASSET,
    amount = USDCtotal,
  )

def appendSEP6sellOpToTxnEnvelope(transactionEnvelope, myAskID, yUSDCtotal):
  print("Tries to do a SEP-6 sell")
  # cancel outstanding sell offer
  if(myAskID):
    transactionEnvelope.append_manage_sell_offer_op( # edge test here cancelling a sell vs. buy offer
      selling = yUSDC_ASSET,
      buying = USDC_ASSET,
      amount = 0,
      price = 1,
      offer_id = myAskID,
    )
  # do sep 6 exchange
  ultrastellarServer = "https://" + TRANSFER_SERVER + "/withdraw"
  response = requests.post(ultrastellarServer + "?asset_code=yUSDC&account=" + BT_TREASURY)
  # parse response.json()["how"]
  
  
  transactionEnvelope.append_payment_op( #
    destination = 1, # 
    asset = yUSDC_ASSET,
    amount = yUSDCtotal,
  )

main()