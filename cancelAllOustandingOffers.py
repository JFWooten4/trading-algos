from stellar_sdk import Asset, Keypair, Network, Server, TransactionBuilder
from pprint import pprint
import requests, json, sys

BT_TREASURY = "GD2OUJ4QKAPESM2NVGREBZTLFJYMLPCGSUHZVRMTQMF5T34UODVHPRCY"
HORIZON_INST = "horizon.stellar.org"
MAX_SEARCH = "200"
TXN_FEE_STROOPS = 5000

def main():
  try:
    SECRET = sys.argv[1]
  except:
    print("Failed without key")
    return -1
  offerData = []
  requestAddress = "https://" + HORIZON_INST + "/accounts/" + BT_TREASURY
  data = requests.get(requestAddress).json()
  requestAddress = data["_links"]["offers"]["href"].replace("{?cursor,limit,order}", "?limit={}".format(MAX_SEARCH))
  data = requests.get(requestAddress).json()
  outstandingOffers = data["_embedded"]["records"]
  for offers in outstandingOffers:
    offerData.append(int(offers['id']))
    oD = offers["buying"] # offerBuyingAssetDict
    offerData.append(Asset(oD["asset_code"], oD["asset_issuer"]))
    oD = offers["selling"] # offerSellingAssetDict
    offerData.append(Asset(oD["asset_code"], oD["asset_issuer"]))
  
  server = Server(horizon_url = "https://" + HORIZON_INST)
  treasury = server.load_account(account_id = BT_TREASURY)
  signing_keypair = Keypair.from_secret(SECRET)
  transaction = TransactionBuilder(
    source_account = treasury,
    network_passphrase = Network.PUBLIC_NETWORK_PASSPHRASE,
    base_fee = TXN_FEE_STROOPS,
  )
  for offerIDs, buyingAssets, sellingAssets in zip(*[iter(offerData)]*3):
    transaction.append_manage_buy_offer_op(
      selling = sellingAssets,
      buying = buyingAssets,
      amount = "0",
      price = "69",
      offer_id = offerIDs,
    )
    transaction = transaction.set_timeout(30).build()
    transaction.sign(signing_keypair)
    server.submit_transaction(transaction)
    print("Successfully cancelled {} offers".format(len(offerData)/3))
main()