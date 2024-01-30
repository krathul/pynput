# coding=utf-8
# pynput
# Copyright (C) 2015-2022 Moses Palmér
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
"""
Utility functions and classes for the *uinput* backend.
"""

# pylint: disable=R0903
# We implement stubs

import evdev


# Check that we have permissions to continue
def _check():
    # TODO: Implement!
    pass
_check()
del _check


class ListenerMixin(object):
    """A mixin for *uinput* event listeners.

    Subclasses should set a value for :attr:`_EVENTS` and implement
    :meth:`_handle`.
    """
    #: The events for which to listen
    _EVENTS = tuple()

    def __init__(self, *args, **kwargs):
        super(ListenerMixin, self).__init__(*args, **kwargs)
        self._dev = self._get_device()
        if self.suppress:
            self._dev.grab()

    def _run(self):
        for event in self._dev.read_loop():
            if event.type in self._EVENTS:
                self._handle(event)

    def _stop_platform(self):
        self._dev.close()

    def _get_device(self, paths):
        """ Device specific implementation
        Attempts to load a device.

        :param paths: A list of paths.

        :return: a compatible device
        """
        raise NotImplementedError()

    def _handle(self, event):
        """Handles a single event.

        This method should call one of the registered event callbacks.

        :param event: The event.
        """
        raise NotImplementedError()
