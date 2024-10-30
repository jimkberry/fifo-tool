
import sys
import pytest
import pytest_mock
from datetime import datetime
from typing import List, Dict, Any

from models.acquisition import Acquisition
from models.disposition import Disposition
from models.stash import Stash

from stash_test_data import TEST_ACQ_1, TEST_ACQ_2, TEST_DISP_1, TEST_DISP_2, STASH_JSON_DICT_1


def test_stash_init():
    #default
    s = Stash()
    assert s.currency_name == ""
    assert len(s.acquisitions) == 0
    assert len(s.dispositions) == 0

    # w/params
    # s = Stash("BTC", acqs, disps)
    # assert s.currency_name == "BTC"
    # assert len(s.acquisitions) == 1
    # assert len(s.dispositions) == 1
    # assert isinstance(s.acquisitions[0], Acquisition)
    # assert isinstance(s.dispositions[0], Disposition)

def test_stash_from_json_dict(mocker):

    spyA = mocker.spy(Acquisition, "from_json_dict")
    spyD = mocker.spy(Disposition, "from_json_dict")

    s = Stash.from_json_dict(STASH_JSON_DICT_1)

    assert s.currency_name == "BTC"
    assert len(s.acquisitions) == 2  # [TEST_ACQ_1, TEST_ACQ2]
    assert len(s.dispositions) == 2  # [TEST_DISP_1, TEST_DISP_2]
    assert isinstance(s.acquisitions[0], Acquisition)
    assert isinstance(s.dispositions[0], Disposition)

    assert spyA.call_count == 2
    assert spyD.call_count == 2




