from stellar_sdk import Asset, Keypair, Network, Server, TransactionBuilder
from decimal import Decimal, getcontext
import requests, json, time, math
from pprint import pprint

BT_TREASURY = "GDRM3MK6KMHSYIT4E2AG2S2LWTDBJNYXE4H72C7YTTRWOWX5ZBECFWO7" # ...
yUSDC_ISSUER = "GDGTVWSM4MGS4T7Z6W4RPWOCHE2I6RDFCIFZGS3DOA63LWQTRNZNTTFF"
USDC_ISSUER = "GA5ZSEJYB37JRC5AVCIA5MOP4RHTM335X2KGX3IHOJAPP5RE34K4KZVN"
SECRET = "SBTPLXTXJDMJOXFPYU2ANLZI2ARDPHFKPKK4MJFYVZVBLXYM5AIP3LPK"

TRANSFER_SERVER = "ultrastellar.com/sep6"
HORIZON_INST = "horizon.stellar.org"
MAX_SEARCH = "200"

MIN_MEANINGFUL_SIZE = 690.42
MIN_INCREMENT = .0000001
TXN_FEE_STROOPS = 5000
MIN_BID = .995
MAX_BID = .99993
MIN_OFFER = 1.00007
MAX_OFFER = 1.42

yUSDCasset = Asset("yUSDC", yUSDC_ISSUER)
USDCasset = Asset("USDC", USDC_ISSUER)

def main():
  getcontext().prec = 7
  myBid = USDCbuyOutstanding = USDCavailable = yUSDCsellOutstanding = yUSDCavailable = Decimal(0)
  myAsk = Decimal(100)
  server = Server(horizon_url = "https://" + HORIZON_INST)
  treasury = server.load_account(account_id = BT_TREASURY)
  try:
    SECRET = sys.argv[1]
  except:
    print("Running without key. Usage: python3 mm-yUSDC-USDC.py $secret")
  finally:
    print("Starting yUSDC-USDC market making algorithm from {:.1f}bps spread".format(10000*(MIN_OFFER-MAX_BID)))
  
  # Establish ultrastellar session authentication
  authAddr = "https://ultrastellar.com/auth?account=" + BT_TREASURY
  response = requests.get(authAddr)
  txn = response.json()["transaction"]
  response = requests.post(authAddr, json={"transaction": transaction.sign(treasury)})
  try:
    token = response.json()["token"]
  else: 
    print("UltraStellar authentication failed. Exiting now")
    return -1
  # Start algo
  while(True):
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
      if(offers["selling"]["asset_code"] == "yUSDC" and offers["buying"]["asset_code"] == "USDC"):
        myAsk = Decimal(offers["price"])
        myAskID = int(offers['id'])
      elif(offers["selling"]["asset_code"] == "USDC" and offers["buying"]["asset_code"] == "yUSDC"):
        myBid = Decimal(offers["price_r"]["d"]) / Decimal(offers["price_r"]["n"]) # Always buying in terms of selling
        myBidID = int(offers['id'])
    
    requestAddress = "https://" + HORIZON_INST + "/order_book?selling_asset_type=credit_alphanum12&selling_asset_code=yUSDC&selling_asset_issuer=" + yUSDC_ISSUER + "&buying_asset_type=credit_alphanum4&buying_asset_code=USDC&buying_asset_issuer=" + USDC_ISSUER + "&limit=" + MAX_SEARCH    
    data = requests.get(requestAddress).json()
    bidsFromStellar = data["bids"]
    asksFromStellar = data["asks"]
    
    highestMeaningfulBid = MIN_BID
    for bids in bidsFromStellar:
      if(Decimal(bids["amount"]) > MIN_MEANINGFUL_SIZE and Decimal(bids["price"]) > highestMeaningfulBid):
        highestMeaningfulBid = Decimal(bids["price"])
    
    lowestMeaningfulOffer = MAX_OFFER
    for offers in asksFromStellar:
      if(Decimal(offers["amount"]) > MIN_MEANINGFUL_SIZE and Decimal(offers["price"]) < lowestMeaningfulOffer):
        lowestMeaningfulOffer = Decimal(offers["price"])

    # INIT COMPLETE...
    # BEGIN TRADING LOGIC


    print(USDCbuyOutstanding)
    print(USDCavailable)
    print(USDCtotal)
    
    print(yUSDCsellOutstanding)
    print(yUSDCavailable)
    print(yUSDCtotal)
    
    if(highestMeaningfulBid > myBid):
      transaction = TransactionBuilder(
        source_account = treasury,
        network_passphrase = Network.PUBLIC_NETWORK_PASSPHRASE,
        base_fee = TXN_FEE_STROOPS,
      )
      if(highestMeaningfulBid >= MAX_BID and USDCavailable > MIN_MEANINGFUL_SIZE):
        # do sep 6 exchange
        ultrastellarServer = "https://" + TRANSFER_SERVER + "/deposit"
        response = requests.get(ultrastellarServer + "?asset_code=yUSDC&account=" + BT_TREASURY)
        # parse response.json()["how"]
        
      else:
        transaction.append_manage_sell_offer_op(
          selling = USDCasset,
          buying = yUSDCasset,
          amount = USDCtotal,
          price = highestMeaningfulBid + Decimal(MIN_INCREMENT),
          offer_id = myBidID
        )

    elif(lowestMeaningfulOffer < myAsk):
      transaction = TransactionBuilder(
        source_account = treasury,
        network_passphrase = Network.PUBLIC_NETWORK_PASSPHRASE,
        base_fee = TXN_FEE_STROOPS,
      )
      if(lowestMeaningfulOffer <= MAX_OFFER and yUSDCavailable > MIN_MEANINGFUL_SIZE):
        # do sep 6 exchange
        ultrastellarServer = "https://" + TRANSFER_SERVER + "/withdraw"
        response = requests.get(ultrastellarServer + "?asset_code=yUSDC&account=" + BT_TREASURY)
        # parse response.json()["how"]
        
      else:
        transaction.append_manage_buy_offer_op(
          selling = yUSDCasset,
          buying = USDCasset,
          amount = yUSDCtotal,
          price = lowestMeaningfulOffer - Decimal(MIN_INCREMENT),
          offer_id = myBidID
        )
    
    time.sleep(32)

main()