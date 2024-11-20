
# test data

#Acquisitions
TEST_ACQ_1 = {
    "timestamp": 1445538780.0,
    "asset": "BTC",
    "asset_amount": 75.51075,
    "asset_price": 274.18,
    "fees": 0.0,
    "reference": "CB Ref: DEEDAB",
    "comment": ""
}

TEST_ACQ_2 = {
    "timestamp": 1448997540.0,
    "asset": "BTC",
    "asset_amount": 27.76054701,
    "asset_price": 363.89,
    "fees": 0.0,
    "reference": "CB Ref: 12345678",
    "comment": ""
}

# dispositions
TEST_DISP_1 = {
    "timestamp": 1445540160.0,
    "asset": "BTC",
    "asset_amount": 34.92438215,
    "asset_price": 274.76390433,
    "fees": 95.96,
    "reference": "CB Ref: YBFY7P4C",
    "comment": ""
}

TEST_DISP_2 = {
    "timestamp": 1469778541.0,
    "asset": "BTC",
    "asset_amount": 7.12687025,
    "asset_price": 657.48,
    "fees": 0.0,
    "comment": "",
    "reference": "gd 2469644b-ce15-455c-ad0d-e8abfccbf948"
}

STASH_JSON_DICT_1 = {
  "asset": "BTC",
  "title": "Stash 1",
  "acquisitions": [TEST_ACQ_1, TEST_ACQ_2],
  "dispositions": [TEST_DISP_1, TEST_DISP_2]
}


STASH_JSON_DICT_2 = {
  "asset": "BTC",
  "title": "Stash 2",
  "acquisitions": [
    {
      "timestamp": "12/01/2015 14:19:00",
      "asset": "BTC",
      "asset_amount": 27.76054701,
      "asset_price": 363.89,
      "fees": 0.0,
      "comment": "",
      "reference": "CB Ref: 12345679"
    },
    {
      "timestamp": 1451316900.0,
      "asset": "BTC",
      "asset_amount": 23.48877188,
      "asset_price": 425.08,
      "fees": 0.0,
      "reference": "CB Ref: 123ddddd",
      "comment": ""
    },
    {
      "timestamp": 1455035940.0,
      "asset": "BTC",
      "asset_amount": 13.33640657,
      "asset_price": 372.37,
      "fees": 0.0,
      "reference": "CB Ref: 0012435",
      "comment": ""
    },
    {
      "timestamp": 1455737160.0,
      "asset": "BTC",
      "asset_amount": 11.8768791,
      "asset_price": 418.75,
      "fees": 0.0,
      "reference": "CB Ref: 23234334",
      "comment": ""
    }],
    "dispositions": [
      {
      "timestamp": 1469778541.0,
      "asset": "BTC",
      "asset_amount": 7.12687025,
      "asset_price": 657.48,
      "fees": 0.0,
      "comment": "",
      "reference": "gd 2469644b-ce15-455c-ad0d-e8abfccbf948"
      },
      {
      "timestamp": 1470852480,
      "asset": "BTC",
      "asset_amount": 7.85967878,
      "asset_price": 593.91,
      "fees": 0.0,
      "comment": "",
      "reference": "gd 66289921-0a3c-44c6-b9cf-582cf53469ca"
      }
    ]
}




