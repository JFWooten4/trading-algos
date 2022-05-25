from stellar_sdk import Asset, Keypair, Network, Server, TransactionBuilder
from decimal import Decimal, getcontext
import requests, json, time, sys
from pprint import pprint
import sep10

BT_TREASURY = "GD2OUJ4QKAPESM2NVGREBZTLFJYMLPCGSUHZVRMTQMF5T34UODVHPRCY"

yUSDC_ISSUER = "GDGTVWSM4MGS4T7Z6W4RPWOCHE2I6RDFCIFZGS3DOA63LWQTRNZNTTFF"
USDC_ISSUER = "GA5ZSEJYB37JRC5AVCIA5MOP4RHTM335X2KGX3IHOJAPP5RE34K4KZVN"

TRANSFER_SERVER = "ultrastellar.com/sep6"
HORIZON_INST = "horizon.stellar.org"
MAX_SEARCH = "200"

MIN_MEANINGFUL_SIZE = 500
MIN_INCREMENT = Decimal(".0000001")
TXN_FEE_STROOPS = 5000
MIN_BID = 0.0000001
MAX_BID = .99993
MIN_OFFER = 1.00007
MAX_OFFER = 42

yUSDCasset = Asset("yUSDC", yUSDC_ISSUER)
USDCasset = Asset("USDC", USDC_ISSUER)

def main():
  #getcontext().prec = 7
  myBid = USDCbuyOutstanding = USDCavailable = yUSDCsellOutstanding = yUSDCavailable = Decimal(0)
  myAsk = Decimal(100)
  try:
    SECRET = sys.argv[1]
  except:
    SECRET = "SBTPLXTXJDMJOXFPYU2ANLZI2ARDPHFKPKK4MJFYVZVBLXYM5AIP3LPK"
    print("Running without key. Usage: python3 mm-yUSDC-USDC.py $secret")
  print("Starting yUSDC-USDC market making algorithm from {:.1f}bps spread".format(10000*(MIN_OFFER-MAX_BID)))
  server = Server(horizon_url = "https://" + HORIZON_INST)
  treasury = server.load_account(account_id = BT_TREASURY)
  signing_keypair = Keypair.from_secret(SECRET)
  # Establish ultrastellar session authentication
#  authAddr = "https://ultrastellar.com/auth?account=" + BT_TREASURY
#  response = requests.get(authAddr)
#  transaction = response.json()["transaction"].to_xdr_object()
#  transaction.sign(signing_keypair)
#  pprint(transaction)
#  response = requests.post(authAddr, json={"transaction": transaction})
#  try:
#    token = response.json()["token"]
#  except: 
#    print("UltraStellar authentication failed. Exiting now")
#    return -1
  print(signing_keypair)
  webauth = sep10.Sep10("yUSDC", yUSDC_ISSUER, SECRET)
  print(webauth)
  token = webauth.run_auth()
  print(token)
  # Start algo
  # while timeInUnix < exprTime -> recursive call to main
  while(True):
    #time.sleep(32)
    transaction = ""
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

    # INIT COMPLETE...
    # BEGIN TRADING LOGIC
    
    if(highestMeaningfulCompetingBid > myBid):
      transaction = TransactionBuilder(
        source_account = treasury,
        network_passphrase = Network.PUBLIC_NETWORK_PASSPHRASE,
        base_fee = TXN_FEE_STROOPS,
      )
      if(1): # if(highestMeaningfulCompetingBid >= MAX_BID and USDCavailable > MIN_MEANINGFUL_SIZE):
        print("Tries to do a SEP-6 buy")
        # cancel outstaning buy offer (then use total USDC)
        if(myBidID):
          transaction.append_manage_buy_offer_op(
            selling = USDCasset,
            buying = yUSDCasset,
            amount = 0,
            price = 1,
            offer_id = myBidID,
          )
        
        ultrastellarServer = "https://" + TRANSFER_SERVER + "/deposit"
        response = requests.get(ultrastellarServer + "?asset_code=yUSDC&account=" + BT_TREASURY)
        # parse response.json()["how"]
        pprint(response)
        return 1
        transaction.append_payment_op( #
          destination = 1, # 
          asset = USDCasset,
          amount = USDCtotal,
        )
        
      else:
        transaction.append_manage_sell_offer_op(
          selling = USDCasset,
          buying = yUSDCasset,
          amount = USDCtotal,
          price = highestMeaningfulCompetingBid + MIN_INCREMENT,
          offer_id = myBidID,
        )

    elif(lowestMeaningfulCompetingOffer < myAsk):
      transaction = TransactionBuilder(
        source_account = treasury,
        network_passphrase = Network.PUBLIC_NETWORK_PASSPHRASE,
        base_fee = TXN_FEE_STROOPS,
      )
      if(lowestMeaningfulCompetingOffer <= MIN_OFFER and yUSDCavailable > MIN_MEANINGFUL_SIZE):
        print("Tries to do a SEP-6 sell")
        continue
        # cancel outstanding sell offer
        if(myAskID):
          transaction.append_manage_buy_offer_op(
            selling = yUSDCasset,
            buying = USDCasset,
            amount = 0,
            price = 1,
            offer_id = myAskID,
          )
        # do sep 6 exchange
        ultrastellarServer = "https://" + TRANSFER_SERVER + "/withdraw"
        response = requests.get(ultrastellarServer + "?asset_code=yUSDC&account=" + BT_TREASURY)
        # parse response.json()["how"]
        
        
        transaction.append_payment_op( #
          destination = 1, # 
          asset = yUSDCasset,
          amount = yUSDCtotal,
        )
        
        
      else:
        transaction.append_manage_buy_offer_op(
          selling = yUSDCasset,
          buying = USDCasset,
          amount = yUSDCtotal,
          price = lowestMeaningfulCompetingOffer - MIN_INCREMENT,
          offer_id = myBidID,
        )
    
    if(transaction):
      transaction = transaction.set_timeout(30).build()
      transaction.sign(signing_keypair)
      # server.submit_transaction(transaction)
      print("Manage offer set at {} (+-1)".format(lowestMeaningfulCompetingOffer if highestMeaningfulCompetingBid < myBid else highestMeaningfulCompetingBid))
      # print(transaction.to_xdr())

main()