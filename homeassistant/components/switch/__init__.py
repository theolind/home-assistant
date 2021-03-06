"""
homeassistant.components.switch
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Component to interface with various switches that can be controlled remotely.
"""
import logging
from datetime import timedelta

from homeassistant.helpers.entity_component import EntityComponent
from homeassistant.helpers.entity import ToggleEntity

from homeassistant.const import (
    STATE_ON, SERVICE_TURN_ON, SERVICE_TURN_OFF, ATTR_ENTITY_ID)
from homeassistant.components import group, discovery, wink, isy994

DOMAIN = 'switch'
DEPENDENCIES = []
SCAN_INTERVAL = 30

GROUP_NAME_ALL_SWITCHES = 'all switches'
ENTITY_ID_ALL_SWITCHES = group.ENTITY_ID_FORMAT.format('all_switches')

ENTITY_ID_FORMAT = DOMAIN + '.{}'

ATTR_TODAY_MWH = "today_mwh"
ATTR_CURRENT_POWER_MWH = "current_power_mwh"

MIN_TIME_BETWEEN_SCANS = timedelta(seconds=10)

# Maps discovered services to their platforms
DISCOVERY_PLATFORMS = {
    discovery.SERVICE_WEMO: 'wemo',
    wink.DISCOVER_SWITCHES: 'wink',
    isy994.DISCOVER_SWITCHES: 'isy994',
}

PROP_TO_ATTR = {
    'current_power_mwh': ATTR_CURRENT_POWER_MWH,
    'today_power_mw': ATTR_TODAY_MWH,
}

_LOGGER = logging.getLogger(__name__)


def is_on(hass, entity_id=None):
    """ Returns if the switch is on based on the statemachine. """
    entity_id = entity_id or ENTITY_ID_ALL_SWITCHES
    return hass.states.is_state(entity_id, STATE_ON)


def turn_on(hass, entity_id=None):
    """ Turns all or specified switch on. """
    data = {ATTR_ENTITY_ID: entity_id} if entity_id else None
    hass.services.call(DOMAIN, SERVICE_TURN_ON, data)


def turn_off(hass, entity_id=None):
    """ Turns all or specified switch off. """
    data = {ATTR_ENTITY_ID: entity_id} if entity_id else None
    hass.services.call(DOMAIN, SERVICE_TURN_OFF, data)


def setup(hass, config):
    """ Track states and offer events for switches. """
    component = EntityComponent(
        _LOGGER, DOMAIN, hass, SCAN_INTERVAL, DISCOVERY_PLATFORMS,
        GROUP_NAME_ALL_SWITCHES)
    component.setup(config)

    def handle_switch_service(service):
        """ Handles calls to the switch services. """
        target_switches = component.extract_from_service(service)

        for switch in target_switches:
            if service.service == SERVICE_TURN_ON:
                switch.turn_on()
            else:
                switch.turn_off()

            if switch.should_poll:
                switch.update_ha_state(True)

    hass.services.register(DOMAIN, SERVICE_TURN_OFF, handle_switch_service)
    hass.services.register(DOMAIN, SERVICE_TURN_ON, handle_switch_service)

    return True


class SwitchDevice(ToggleEntity):
    """ Represents a switch within Home Assistant. """
    # pylint: disable=no-self-use

    @property
    def current_power_mwh(self):
        """ Current power usage in mwh. """
        return None

    @property
    def today_power_mw(self):
        """ Today total power usage in mw. """
        return None

    @property
    def device_state_attributes(self):
        """ Returns device specific state attributes. """
        return None

    @property
    def state_attributes(self):
        """ Returns optional state attributes. """
        data = {}

        for prop, attr in PROP_TO_ATTR.items():
            value = getattr(self, prop)
            if value:
                data[attr] = value

        device_attr = self.device_state_attributes

        if device_attr is not None:
            data.update(device_attr)

        return data
