
# test data

#Acquisitions
TEST_ACQ_1 = {
    "timestamp": "10/22/2015 14:33:00",
    "asset_amount": 75.51075,
    "asset_price": 274.18,
    "fees": 0.0,
    "comment": ""
}

TEST_ACQ_2 = {
    "timestamp": "12/01/2015 14:19:00",
    "asset_amount": 27.76054701,
    "asset_price": 363.89,
    "fees": 0.0,
    "comment": ""
}

# dispositions
TEST_DISP_1 = {
    "timestamp": "10/22/2015 14:56:00",
    "asset_amount": 34.92438215,
    "asset_price": 274.76390433,
    "fees": "95.96",
    "reference": "CB Ref: YBFY7P4C",
    "comment": ""
}

TEST_DISP_2 = {
    "timestamp": "07/29/2016 03:49:01",
    "asset_amount": 7.12687025,
    "asset_price": 657.48,
    "fees": 0.0,
    "comment": "",
    "reference": "gd 2469644b-ce15-455c-ad0d-e8abfccbf948"
}

STASH_JSON_DICT_1 = {
  "currency_name": "BTC",
  "acquisitions": [TEST_ACQ_1, TEST_ACQ_2],
  "dispositions": [TEST_DISP_1, TEST_DISP_2]
}


STASH_JSON_DICT_2 = {
  "currency_name": "BTC",
  "acquisitions": [
    {
      "timestamp": "12/01/2015 14:19:00",
      "asset_amount": 27.76054701,
      "asset_price": 363.89,
      "fees": 0.0,
      "comment": ""
    },
    {
      "timestamp": "12/28/2015 10:35:00",
      "asset_amount": 23.48877188,
      "asset_price": 425.08,
      "fees": 0.0,
      "comment": ""
    },
    {
      "timestamp": "02/09/2016 11:39:00",
      "asset_amount": 13.33640657,
      "asset_price": 372.37,
      "fees": 0.0,
      "comment": ""
    },
    {
      "timestamp": "02/17/2016 14:26:00",
      "asset_amount": 11.8768791,
      "asset_price": 418.75,
      "fees": 0.0,
      "comment": ""
    }],
    "dispositions": [
      {
      "timestamp": "07/29/2016 03:49:01",
      "asset_amount": 7.12687025,
      "asset_price": 657.48,
      "fees": 0.0,
      "comment": "",
      "reference": "gd 2469644b-ce15-455c-ad0d-e8abfccbf948"
      },
      {
      "timestamp": "08/10/2016 14:08:00",
      "asset_amount": 7.85967878,
      "asset_price": 593.91,
      "fees": 0.0,
      "comment": "",
      "reference": "gd 66289921-0a3c-44c6-b9cf-582cf53469ca"
      }
    ]
}




