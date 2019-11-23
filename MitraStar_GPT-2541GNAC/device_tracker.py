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

from homeassistant.components.device_tracker import (DOMAIN, PLATFORM_SCHEMA, DeviceScanner)
from homeassistant.const import (CONF_HOST, CONF_PASSWORD, CONF_USERNAME, HTTP_HEADER_X_REQUESTED_WITH)
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
        self.parse_dhcp = re.compile(r'<td>([0-9a-zA-Z\-._]+)<\/td><td>([0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2})<\/td><td>([0-9]+.[0-9]+.[0-9]+.[0-9]+.[0-9]+)')

        self.host = host
        self.username = username
        self.password = password

        self.LOGIN_URL = 'http://{ip}/login-login.cgi'.format(**{'ip': self.host})
        self.headers1 = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36'}

        self.last_results = {}
        self.hostnames = {}
        self.success_init = self._update_info()

    def scan_devices(self):
        """Scan for new devices and return a list with found device IDs."""
        self._update_info()
        return self.last_results


    def get_device_name(self, device):
        """This router doesn't save the name of the wireless device."""
        match = [element[0] for element in self.hostnames if element[1].lower()==device]
        if len(match) > 0:
            device_name = match[0]
        else:
            device_name =  None
        return device_name

    def _update_info(self):
        """Ensure the information from the MitraStar router is up to date.
        Return boolean if scanning successful.
        """
        _LOGGER.info('Checking MitraStar GPT-2541GNAC Router')

        data, hostnames = self.get_MitraStar_info()
        if not data:
            return False

        self.last_results = data
        self.hostnames = hostnames
        return True

    def _read_table(self, session, url):
        response = session.get(url, headers=self.headers1)
        if response.status_code == 200:
            response_string = str(response.content, "utf-8")
            return response_string
        else:
            este_error = 'Error al conectar al Router desde la url: {}'.format(url)
            _LOGGER.error(este_error)



    def get_MitraStar_info(self):
        """Retrieve data from MitraStar GPT-2541GNAC Router."""

        # headers2 = dict(referer=self.LOGIN_URL)

        username1 = str(self.username)
        password1 = str(self.password)

        sessionKey = base64.b64encode(
            '{user}:{pass}'.format(**{
                'user': username1,
                'pass': password1
            }).encode()
        )
        data1 = {
            'sessionKey': sessionKey,
            'pass': ''
        }

        # Creo la sesion y hago login
        session1 = requests.Session()
        login_response = session1.post(self.LOGIN_URL, data=data1, headers=self.headers1)
       
        # Si conecta bien con el Router
        #if str(login_response) == '<Response [200]>':
        if login_response.status_code == 200:

            # # Pagina1
            url1 = 'http://{}/wlextstationlist.cmd?action=view&wlSsidIdx=2'.format(self.host)
            url2 = 'http://{}/wlextstationlist.cmd?action=view&wlSsidIdx=1'.format(self.host)
            url3 = 'http://{}/arpview.cmd'.format(self.host)
            url4 = 'http://{}/dhcpinfo.html'.format(self.host)

            result1 = self._read_table(session1, url1).lower()
            MAC_Address1 = self.parse_macs.findall(result1)

            result2 = self._read_table(session1, url2).lower()
            MAC_Address2 = self.parse_macs.findall(result2)

            result3 = self._read_table(session1, url3).lower()
            MAC_Address3 = self.parse_macs.findall(result3)

            result4 = self._read_table(session1, url4)
            result4 = result4.replace('\n ','').replace(' ','')
            hostnames = self.parse_dhcp.findall(result4)


            # Lo Uno Todo y Borro Duplicados. Así medio raro....
            MAC_Address1.extend([element for element in MAC_Address2 if element not in MAC_Address1])
            MAC_Address1.extend([element for element in MAC_Address3 if element not in MAC_Address1])
            _LOGGER.info('MitraStar GPT-2541GNAC Router: Found %d devices' %len(MAC_Address1))


        else:
            MAC_Address1 = None
            _LOGGER.error('Error connecting to the router...')

        # Cierro la sesion
        #session1.close()

        return MAC_Address1, hostnames

