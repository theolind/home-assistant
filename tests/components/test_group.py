"""
tests.test_component_group
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Tests the group compoments.
"""
# pylint: disable=protected-access,too-many-public-methods
import unittest
import logging

import homeassistant as ha
from homeassistant.const import STATE_ON, STATE_OFF, STATE_HOME, STATE_UNKNOWN
import homeassistant.components.group as group


def setUpModule():   # pylint: disable=invalid-name
    """ Setup to ignore group errors. """
    logging.disable(logging.CRITICAL)


class TestComponentsGroup(unittest.TestCase):
    """ Tests homeassistant.components.group module. """

    def setUp(self):  # pylint: disable=invalid-name
        """ Init needed objects. """
        self.hass = ha.HomeAssistant()

        self.hass.states.set('light.Bowl', STATE_ON)
        self.hass.states.set('light.Ceiling', STATE_OFF)
        test_group = group.Group(
            self.hass, 'init_group', ['light.Bowl', 'light.Ceiling'], False)

        self.group_entity_id = test_group.entity_id

    def tearDown(self):  # pylint: disable=invalid-name
        """ Stop down stuff we started. """
        self.hass.stop()

    def test_setup_group_with_mixed_groupable_states(self):
        """ Try to setup a group with mixed groupable states """
        self.hass.states.set('device_tracker.Paulus', STATE_HOME)
        group.setup_group(
            self.hass, 'person_and_light',
            ['light.Bowl', 'device_tracker.Paulus'])

        self.assertEqual(
            STATE_ON,
            self.hass.states.get(
                group.ENTITY_ID_FORMAT.format('person_and_light')).state)

    def test_setup_group_with_a_non_existing_state(self):
        """ Try to setup a group with a non existing state """
        grp = group.setup_group(
            self.hass, 'light_and_nothing',
            ['light.Bowl', 'non.existing'])

        self.assertEqual(STATE_ON, grp.state)

    def test_setup_group_with_non_groupable_states(self):
        self.hass.states.set('cast.living_room', "Plex")
        self.hass.states.set('cast.bedroom', "Netflix")

        grp = group.setup_group(
            self.hass, 'chromecasts',
            ['cast.living_room', 'cast.bedroom'])

        self.assertEqual(STATE_UNKNOWN, grp.state)

    def test_setup_empty_group(self):
        """ Try to setup an empty group. """
        grp = group.setup_group(self.hass, 'nothing', [])

        self.assertEqual(STATE_UNKNOWN, grp.state)

    def test_monitor_group(self):
        """ Test if the group keeps track of states. """

        # Test if group setup in our init mode is ok
        self.assertIn(self.group_entity_id, self.hass.states.entity_ids())

        group_state = self.hass.states.get(self.group_entity_id)
        self.assertEqual(STATE_ON, group_state.state)
        self.assertTrue(group_state.attributes[group.ATTR_AUTO])

    def test_group_turns_off_if_all_off(self):
        """
        Test if the group turns off if the last device that was on turns off.
        """
        self.hass.states.set('light.Bowl', STATE_OFF)

        self.hass.pool.block_till_done()

        group_state = self.hass.states.get(self.group_entity_id)
        self.assertEqual(STATE_OFF, group_state.state)

    def test_group_turns_on_if_all_are_off_and_one_turns_on(self):
        """
        Test if group turns on if all devices were turned off and one turns on.
        """
        # Make sure all are off.
        self.hass.states.set('light.Bowl', STATE_OFF)
        self.hass.pool.block_till_done()

        # Turn one on
        self.hass.states.set('light.Ceiling', STATE_ON)
        self.hass.pool.block_till_done()

        group_state = self.hass.states.get(self.group_entity_id)
        self.assertEqual(STATE_ON, group_state.state)

    def test_is_on(self):
        """ Test is_on method. """
        self.assertTrue(group.is_on(self.hass, self.group_entity_id))
        self.hass.states.set('light.Bowl', STATE_OFF)
        self.hass.pool.block_till_done()
        self.assertFalse(group.is_on(self.hass, self.group_entity_id))

        # Try on non existing state
        self.assertFalse(group.is_on(self.hass, 'non.existing'))

    def test_expand_entity_ids(self):
        """ Test expand_entity_ids method. """
        self.assertEqual(sorted(['light.ceiling', 'light.bowl']),
                         sorted(group.expand_entity_ids(
                             self.hass, [self.group_entity_id])))

    def test_expand_entity_ids_does_not_return_duplicates(self):
        """ Test that expand_entity_ids does not return duplicates. """
        self.assertEqual(
            ['light.bowl', 'light.ceiling'],
            sorted(group.expand_entity_ids(
                self.hass, [self.group_entity_id, 'light.Ceiling'])))

        self.assertEqual(
            ['light.bowl', 'light.ceiling'],
            sorted(group.expand_entity_ids(
                self.hass, ['light.bowl', self.group_entity_id])))

    def test_expand_entity_ids_ignores_non_strings(self):
        """ Test that non string elements in lists are ignored. """
        self.assertEqual([], group.expand_entity_ids(self.hass, [5, True]))

    def test_get_entity_ids(self):
        """ Test get_entity_ids method. """
        self.assertEqual(
            ['light.bowl', 'light.ceiling'],
            sorted(group.get_entity_ids(self.hass, self.group_entity_id)))

    def test_get_entity_ids_with_domain_filter(self):
        """ Test if get_entity_ids works with a domain_filter. """
        self.hass.states.set('switch.AC', STATE_OFF)

        mixed_group = group.Group(
            self.hass, 'mixed_group', ['light.Bowl', 'switch.AC'], False)

        self.assertEqual(
            ['switch.ac'],
            group.get_entity_ids(
                self.hass, mixed_group.entity_id, domain_filter="switch"))

    def test_get_entity_ids_with_non_existing_group_name(self):
        """ Tests get_entity_ids with a non existing group. """
        self.assertEqual([], group.get_entity_ids(self.hass, 'non_existing'))

    def test_get_entity_ids_with_non_group_state(self):
        """ Tests get_entity_ids with a non group state. """
        self.assertEqual([], group.get_entity_ids(self.hass, 'switch.AC'))

    def test_group_being_init_before_first_tracked_state_is_set_to_on(self):
        """ Test if the group turns on if no states existed and now a state it is
            tracking is being added as ON. """
        test_group = group.Group(
            self.hass, 'test group', ['light.not_there_1'])

        self.hass.states.set('light.not_there_1', STATE_ON)

        self.hass.pool.block_till_done()

        group_state = self.hass.states.get(test_group.entity_id)
        self.assertEqual(STATE_ON, group_state.state)

    def test_group_being_init_before_first_tracked_state_is_set_to_off(self):
        """ Test if the group turns off if no states existed and now a state it is
            tracking is being added as OFF. """
        test_group = group.Group(
            self.hass, 'test group', ['light.not_there_1'])

        self.hass.states.set('light.not_there_1', STATE_OFF)

        self.hass.pool.block_till_done()

        group_state = self.hass.states.get(test_group.entity_id)
        self.assertEqual(STATE_OFF, group_state.state)

    def test_setup(self):
        """ Test setup method. """
        self.assertTrue(
            group.setup(
                self.hass,
                {
                    group.DOMAIN: {
                        'second_group': self.group_entity_id + ',light.Bowl'
                    }
                }))

        group_state = self.hass.states.get(
            group.ENTITY_ID_FORMAT.format('second_group'))

        self.assertEqual(STATE_ON, group_state.state)
        self.assertFalse(group_state.attributes[group.ATTR_AUTO])

    def test_groups_get_unique_names(self):
        """ Two groups with same name should both have a unique entity id. """
        grp1 = group.Group(self.hass, 'Je suis Charlie')
        grp2 = group.Group(self.hass, 'Je suis Charlie')

        self.assertNotEqual(grp1.entity_id, grp2.entity_id)
