from stellar_sdk import Asset, Keypair, Network, Server, TransactionBuilder
from decimal import Decimal, getcontext
import requests, json, time, math
from pprint import pprint

BT_TREASURY = "GDRM3MK6KMHSYIT4E2AG2S2LWTDBJNYXE4H72C7YTTRWOWX5ZBECFWO7" # ...
yUSDC_ISSUER = "GDGTVWSM4MGS4T7Z6W4RPWOCHE2I6RDFCIFZGS3DOA63LWQTRNZNTTFF"
USDC_ISSUER = "GA5ZSEJYB37JRC5AVCIA5MOP4RHTM335X2KGX3IHOJAPP5RE34K4KZVN"

HORIZON_INST = "horizon.stellar.org"
MAX_NUM_DECIMALS = "7"
MAX_SEARCH = "200"

MIN_MEANINGFUL_POS = 690.42
TXN_FEE_STROOPS = 5000
MIN_BID = .995
MAX_OFFER = 1.42

SECRET = "SBTPLXTXJDMJOXFPYU2ANLZI2ARDPHFKPKK4MJFYVZVBLXYM5AIP3LPK"

def main():
  getcontext().prec = 7
  try:
    SECRET = sys.argv[1]
  except:
    print("Running without key. Usage: python3 mm-yUSDC-USDC.py $secret")
  finally:
    print("Starting yUSDC-USDC market making algorithm from price range {} to {}".format(MIN_BID, MAX_OFFER))
  while(True):
    #init 
    
    requestAddress = "https://" + HORIZON_INST + "/accounts/" + BT_TREASURY
    data = requests.get(requestAddress).json()
    accountBalances = data["balances"]
    
    for balances in accountBalances:
      if("asset_code" == "USDC"):
        USDCbuyOutstanding = balances["selling_liabilities"]
        USDCavailable = str(Decimal(balances["balance"] - Decimal(USDCbuyOutstanding)))
      elif("asset_code" == "yUSDC"):
        yUSDCsellOutstanding = balances["selling_liabilities"]
        yUSDCavailable = str(Decimal(balances["balance"] - Decimal(USDCsellOutstanding)))

    activeBuyOfferIDs = []
    activeSellOfferIDs = []
    
    requestAddress = data["_links"]["offers"]["href"].replace("{?cursor,limit,order}", "?limit={}".format(MAX_SEARCH))
    data = requests.get(requestAddress).json()
    outstandingOffers = data["_embedded"]["records"]
    while(outstandingOffers != []):
      for offers in outstandingOffers:
        if(offers["selling"]["asset_code"] == "yUSDC" and offers["buying"]["asset_code"] == "USDC"):
          activeSellOfferIDs.append(offers["id"])
        elif(offers["selling"]["asset_code"] == "USDC" and offers["buying"]["asset_code"] == "yUSDC"):
          activeBuyOfferIDs.append(offers["id"])
      # Go to next cursor
      if(length(outstandingOffers) < 200):
        break:
      requestAddress = data["_links"]["next"]["href"].replace("\u0026", "&")
      data = requests.get(requestAddress).json()
      outstandingOffers = data["_embedded"]["records"]
    
    currBuySideBid = ...
    currBuySideOfferID = ...
    
    if(offers["selling"]["asset_code"] == "yUSDC" and offers["buying"]["asset_code"] == "USDC"):
          activeSellOffers[offers["price"]] = offers["amount"]
        elif(offers["selling"]["asset_code"] == "USDC" and offers["buying"]["asset_code"] == "yUSDC"):
          bidPrice = Decimal(1) / Decimal(offers["price"])
          activeBuyOffers[str(bidPrice)] = offers["amount"]
    
    
    requestAddress = "https://" + HORIZON_INST + "/order_book?selling_asset_type=credit_alphanum12&selling_asset_code=yUSDC&selling_asset_issuer=" + yUSDC_ISSUER + "&buying_asset_type=credit_alphanum4&buying_asset_code=USDC&buying_asset_issuer=" + USDC_ISSUER + "&limit=" + MAX_SEARCH
    
    data = requests.get(requestAddress).json()
    
    bidsFromStellar = data["bids"]
    asksFromStellar = data["asks"]
    
    for bids in bidsFromStellar:
    
    
    
    
    bidSide = {} # price, amount
    askSide = {} # price, amount
    
    # get list of bids down to .995
    
    highestMeaningfulBid = MIN_BID;
    
    for bidPrices, amounts in bidSide:
    
    
    
    # get lists of offers up to 1.42
    
    lowestMeaningfulOffer = MAX_OFFER;
 
    for offerPrices, amounts in askSide:
 
      if(roundAmount > MIN_MEANINGFUL_POS && offerPrices < lowestOfferOver1KvolIn5stroopRangeMinVal):
        # logic to adjust sell offer
    
    
    
    # SEP-6 logic
    
    if(highestBidOver1KvolIn5stroopRangeMaxVal >= 1 && USDCbuyOutstanding > 5):
      # go from USDC to yUSDC
    
    
    
    StellarBlockchainBalances = {}
    requestAddress = "https://" + HORIZON_INST + "/accounts?asset=" + queryAsset + ":" + BT_ISSUER + "&limit=" + MAX_SEARCH
    data = requests.get(requestAddress).json()
    blockchainRecords = data["_embedded"]["records"]
    while(blockchainRecords != []):
      for accounts in blockchainRecords:
        accountAddress = accounts["id"]
        for balances in accounts["balances"]:
          try:
            if balances["asset_code"] == queryAsset and balances["asset_issuer"] == BT_ISSUER:
              accountBalance = Decimal(balances["balance"])
          except:
            continue
        StellarBlockchainBalances[accountAddress] = accountBalance
      # Go to next cursor
      requestAddress = data["_links"]["next"]["href"].replace("%3A", ":")
      data = requests.get(requestAddress).json()
      blockchainRecords = data["_embedded"]["records"]
    return StellarBlockchainBalances
    
    
    
    
    
    time.sleep(32)

main()