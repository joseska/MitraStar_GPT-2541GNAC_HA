"""

Support for MitraStar GPT-2541GNAC Router (Movistar Spain).
For more details about this platform, please refer to the documentation at 

"""
import base64
from datetime import datetime
import hashlib
import logging
import re
import requests
import voluptuous as vol

from homeassistant.components.device_tracker import (
    DOMAIN, PLATFORM_SCHEMA, DeviceScanner)
from homeassistant.const import (
    CONF_HOST, CONF_PASSWORD, CONF_USERNAME, HTTP_HEADER_X_REQUESTED_WITH)
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)


PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_HOST): cv.string,
    vol.Required(CONF_PASSWORD): cv.string,
    vol.Required(CONF_USERNAME): cv.string
})


def get_scanner(hass, config):
    # """Validate the configuration and return a TP-Link scanner."""

    scanner = MitraStarDeviceScanner(config[DOMAIN])
    return scanner if scanner.success_init else None


class MitraStarDeviceScanner(DeviceScanner):
    """This class queries a MitraStar GPT-2541GNAC wireless Router (Movistar Spain)."""

    def __init__(self, config):
        """Initialize the scanner."""
        host = config[CONF_HOST]
        username = config[CONF_USERNAME]
        password = config[CONF_PASSWORD]

        self.parse_macs = re.compile(r'([0-9a-fA-F]{2}:' + '[0-9a-fA-F]{2}:' + '[0-9a-fA-F]{2}:' + '[0-9a-fA-F]{2}:' + '[0-9a-fA-F]{2}:' + '[0-9a-fA-F]{2})')

        self.host = host
        self.username = username
        self.password = password

        self.LOGIN_URL = 'http://{ip}/login-login.cgi'.format(**{'ip': self.host})

        self.last_results = {}
        self.success_init = self._update_info()

    def scan_devices(self):
        """Scan for new devices and return a list with found device IDs."""
        self._update_info()
        return self.last_results


    def get_device_name(self, device):
        """This router doesn't save the name of the wireless device."""
        return None

    def _update_info(self):
        """Ensure the information from the MitraStar router is up to date.
        Return boolean if scanning successful.
        """
        _LOGGER.info('Checking MitraStar GPT-2541GNAC Router')

        data = self.get_MitraStar_info()
        if not data:
            return False

        self.last_results = data
        return True



    def get_MitraStar_info(self):
        """Retrieve data from MitraStar GPT-2541GNAC Router."""

        headers1 = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.0; WOW64; rv:24.0) Gecko/20100101 Firefox/24.0'}

        sessionKey = base64.b64encode(
            '{user}:{pass}'.format(**{
                'user': self.username,
                'pass': self.password
            }).encode()
        )
        data1 = {
            'sessionKey': sessionKey,
            'pass': ''
        }

        # Creo la sesion y hago login
        session1 = requests.Session()
        login_response = session1.post(self.LOGIN_URL, data=data1, headers=headers1)

        # Si conecta bien con el Router
        #if str(login_response) == '<Response [200]>':
        if login_response.status_code == 200:
            # Pagina1
            url1 = 'http://{}/wlextstationlist.cmd?action=view&wlSsidIdx=2'.format(self.host)
            response1 = session1.get(url1, headers=headers1, timeout=4)
            response_string1 = str(response1.content)
            result1 = self.parse_macs.findall(response_string1)

            # Pagina2
            url2 = 'http://{}/wlextstationlist.cmd?action=view&wlSsidIdx=1'.format(self.host)
            response2 = session1.get(url2, headers=headers1, timeout=4)
            response_string2 = str(response1.content)
            result2 = self.parse_macs.findall(response_string2)

            # Pagina3
            url3 = 'http://{}/arpview.cmd'.format(self.host)
            response3 = session1.get(url3, headers=headers1, timeout=4)
            response_string3 = str(response3.content)
            result3 = self.parse_macs.findall(response_string3)

            # Lo Uno Todo en "result1" y Borro Duplicados. Así medio raro, pero funciona....
            result1.extend([element for element in result2 if element not in result1])
            result1.extend([element for element in result3 if element not in result1])

        else:
            result1 = None
            _LOGGER.info('Error connecting to the router...')

        # Cierro la sesion
        session1.close()

        return result1


