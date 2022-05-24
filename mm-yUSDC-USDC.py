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

MIN_MEANINGFUL_SIZE = 690.42
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

    requestAddress = data["_links"]["offers"]["href"].replace("{?cursor,limit,order}", "?limit={}".format(MAX_SEARCH))
    data = requests.get(requestAddress).json()
    outstandingOffers = data["_embedded"]["records"]
    for offers in outstandingOffers:
      if(offers["selling"]["asset_code"] == "yUSDC" and offers["buying"]["asset_code"] == "USDC"):
        myAsk = offers["price"]
      elif(offers["selling"]["asset_code"] == "USDC" and offers["buying"]["asset_code"] == "yUSDC"):
        myBid = str(Decimal(offers["price_r"]["d"]) / Decimal(offers["price_r"]["n"])) # Always buying in terms of selling
    
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


    # are we in buy mode or sell mode? 
    print(USDCavailable)
    print(USDCbuyOutstanding)
    print(yUSDCavailable)
    print(yUSDCsellOutstanding)
    break
    
    # SEP-6 logic
    
    # if(highestMeaningfulBid >= 1 and USDCavailable > 5):
      # go from USDC to yUSDC
      # cancel outstaning buy order if any 
      # convert 
      
    # if(lowestMeaningfulOffer <= 1 and yUSDCavailable > 5):
    
    
    

    time.sleep(32)

main()