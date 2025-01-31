import sys
import pytest
from datetime import datetime
from typing import List, Dict, Any

from models.stash import LotState

# init
def test_lot_state_init():

    s = LotState(1)

    assert s.lot_number == 1
    assert s.initial_timestamp == 0
    assert s.initial_balance == 0
    assert s.basis_price == 0
    assert s.update_timestamp == 0
    assert s.update_amount_delta == 0
    assert s.update_asset_price == 0
    assert s.balance == 0


# copy

# acquire

# dispose


# to_json_dict

