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

"""API for reading and changing HID emulation name."""

import os
import asyncio
import yaml

from aiohttp.web import Request
from aiohttp.web import Response

from ....htserver import exposed_http
from ....htserver import make_json_response
from ....yamlconf.loader import load_yaml_file

from ....validators.hw import valid_otg_id
from ....validators.basic import valid_stripped_string


HIDNAME_PATH = "/etc/kvmd/override.d/hidname.yaml"


class HidNameApi:
    def __init__(self, defaults: dict, path: str = HIDNAME_PATH) -> None:
        self.__defaults = {
            "vendor_id": defaults.get("vendor_id"),
            "product_id": defaults.get("product_id"),
            "manufacturer": defaults.get("manufacturer"),
            "product": defaults.get("product"),
            "serial": defaults.get("serial"),
        }
        self.__path = path

    # =====

    def __load(self) -> dict:
        try:
            data = (load_yaml_file(self.__path) or {})
            otg = data.get("otg", {})
        except Exception:
            otg = {}
        result = self.__defaults.copy()
        for key in result:
            if key in otg:
                result[key] = otg[key]
        return result

    def __save(self, data: dict) -> None:
        os.makedirs(os.path.dirname(self.__path), exist_ok=True)
        with open(self.__path, "w") as file:
            yaml.safe_dump({"otg": data}, file)

    async def __delayed_reboot(self) -> None:
        await asyncio.create_subprocess_shell("sync")
        await asyncio.sleep(1)
        await asyncio.create_subprocess_shell("reboot")

    # =====

    @exposed_http("GET", "/hidname")
    async def __get_handler(self, _: Request) -> Response:
        return make_json_response(self.__load())

    @exposed_http("POST", "/hidname")
    async def __set_handler(self, req: Request) -> Response:
        params = {
            "vendor_id": valid_otg_id(req.query.get("vendor_id")),
            "product_id": valid_otg_id(req.query.get("product_id")),
            "manufacturer": valid_stripped_string(req.query.get("manufacturer")),
            "product": valid_stripped_string(req.query.get("product")),
            "serial": valid_stripped_string(req.query.get("serial")),
        }
        self.__save(params)
        asyncio.create_task(self.__delayed_reboot())
        return make_json_response({"status": "Reboot started"})
