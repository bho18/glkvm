# ========================================================================== #
#                                                                            #
#    KVMD - The main PiKVM daemon.                                           #
#                                                                            #
#    Copyright (C) 2018-2024  Maxim Devaev <mdevaev@gmail.com>               #
#                                                                            #
#    This program is free software: you can redistribute it and/or modify    #
#    it under the terms of the GNU General Public License as published by    #
#    the Free Software Foundation, either version 3 of the License, or       #
#    (at your option) any later version.                                     #
#                                                                            #
#    This program is distributed in the hope that it will be useful,         #
#    but WITHOUT ANY WARRANTY; without even the implied warranty of          #
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the           #
#    GNU General Public License for more details.                            #
#                                                                            #
#    You should have received a copy of the GNU General Public License       #
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.  #
#                                                                            #
# ========================================================================== #

"""Tests for HID name API."""

import json
from types import SimpleNamespace

import pytest
from aiohttp.test_utils import make_mocked_request

from kvmd.apps.kvmd.api.hidname import HidNameApi


DEFAULTS = {
    "vendor_id": 0x1D6B,
    "product_id": 0x0104,
    "manufacturer": "GLKVM",
    "product": "Composite KVM Device",
    "serial": "CAFEBABE",
}


@pytest.mark.asyncio
async def test_get_defaults(tmp_path):  # type: ignore
    path = tmp_path / "hidname.yaml"
    api = HidNameApi(DEFAULTS, path=str(path))
    req = make_mocked_request("GET", "/hidname")
    resp = await api._HidNameApi__get_handler(req)
    data = json.loads(resp.text)["result"]
    assert data == DEFAULTS


@pytest.mark.asyncio
async def test_set_and_get(tmp_path):  # type: ignore
    path = tmp_path / "hidname.yaml"
    api = HidNameApi(DEFAULTS, path=str(path))
    req = make_mocked_request(
        "POST",
        "/hidname",
        params={
            "vendor_id": "4660",
            "product_id": "22136",
            "manufacturer": "Test",
            "product": "Device",
            "serial": "ABC",
        },
    )
    await api._HidNameApi__set_handler(req)
    with open(path) as f:
        text = f.read()
    assert "vendor_id: 4660" in text
    req2 = make_mocked_request("GET", "/hidname")
    resp = await api._HidNameApi__get_handler(req2)
    data = json.loads(resp.text)["result"]
    assert data["vendor_id"] == 4660
    assert data["serial"] == "ABC"


@pytest.mark.asyncio
async def test_invalid_value(tmp_path):  # type: ignore
    path = tmp_path / "hidname.yaml"
    api = HidNameApi(DEFAULTS, path=str(path))
    req = make_mocked_request(
        "POST",
        "/hidname",
        params={"vendor_id": "70000", "product_id": "1", "manufacturer": "A", "product": "B", "serial": "C"},
    )
    with pytest.raises(Exception):
        await api._HidNameApi__set_handler(req)
