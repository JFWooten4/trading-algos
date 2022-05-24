from stellar_sdk import Asset, Keypair, Network, Server, TransactionBuilder, TrustLineFlags
from datetime import datetime
from decimal import Decimal
from pprint import pprint
import requests, json

BT_ISSUER = "GDRM3MK6KMHSYIT4E2AG2S2LWTDBJNYXE4H72C7YTTRWOWX5ZBECFWO7"
yUSDC_ISSUER = "GDGTVWSM4MGS4T7Z6W4RPWOCHE2I6RDFCIFZGS3DOA63LWQTRNZNTTFF"
USDC_ISSUER = "GA5ZSEJYB37JRC5AVCIA5MOP4RHTM335X2KGX3IHOJAPP5RE34K4KZVN"

HORIZON_INST = "horizon.stellar.org"
MAX_NUM_DECIMALS = "7"
MAX_SEARCH = "200"

FALLBACK_MIN_FEE = 100
MAX_NUM_TXN_OPS = 100

SECRET = "SBTPLXTXJDMJOXFPYU2ANLZI2ARDPHFKPKK4MJFYVZVBLXYM5AIP3LPK"

def main():
  while(True):
    #init 
    USDCbuyOutstanding = ...
    yUSDCsellOutstanding = ...
    
    currSellSideAsk = ...
    currSellSideOfferID = ...
    
    currBuySideBid = ...
    currBuySideOfferID = ...
    
    USDCavailable = 
    yUSDCavailable = 
    
    bidSide = {} # price, amount
    askSide = {} # price, amount
    
    # get list of bids down to .995
    
    highestBidOver1KvolIn5stroopRangeMaxVal = .995;
    
    for bidPrices, amounts in bidSide:
    
    
    
    # get lists of offers up to 1.42
    
    lowestOfferOver1KvolIn5stroopRangeMinVal = 1.42;
    roundAmount = 0
    for offerPrices, amounts in askSide:
      
      if(offerPrices > minPriceFromRange + ".0000005"):
        minPriceFromRange = offerPrices
        roundAmount = 0
      
      roundAmount += float(amounts)
      
      
      if(roundAmount > 690.42 && offerPrices < currSellSideAsk):
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
    
    
    
    
    
    wait(3)

