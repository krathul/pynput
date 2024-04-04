import enum
import evdev
import os
from evdev import (
    InputDevice,
    InputEvent,
    UInput,
    ecodes
)

from pynput._util.uinput import ListenerMixin
from . import _base

Button = enum.Enum(
    'Button',
    module=__name__,
    names=[
        ('unknown', None),
        ('left', ecodes.BTN_LEFT),
        ('middle', ecodes.BTN_MIDDLE),
        ('right', ecodes.BTN_RIGHT),
    ]
)


class Controller(_base.Controller):
    """
    Takes an argument position getter (couldn't come up with a name), which
    is the function that returns the position of the mouse cursor.
    A function that queries the compositor for cursor position,
    returns a tuple (x,y)
    """

    def __init__(self, _position_getter=None, *args, **kwargs):
        super(Controller, self).__init__(*args, **kwargs)
        self._position_getter = _position_getter
        if (_position_getter is None):
            print("Position getter not assigned, absolute position cannot be set or accessed")
        # position is a 32-bit signed integer, hence the minimum position
        self.INT_MIN32 = -2**31
        self._capabilities = {
            ecodes.EV_KEY: [
                ecodes.BTN_LEFT,
                ecodes.BTN_RIGHT,
                ecodes.BTN_MIDDLE],
            ecodes.EV_REL: [
                ecodes.REL_X,
                ecodes.REL_Y,
                ecodes.REL_WHEEL,
                ecodes.REL_HWHEEL
            ]
        }
        self.device_name = 'PynputMouse'
        self._dev = UInput(self._capabilities, name = self.device_name)

                
    def __del__(self):
        if hasattr(self, '_dev'):
            self._dev.close()

    def _position_get(self):
        """
        libevdev cannot be used to get the position of cursor,
        On cursor position is known only to the compositor.
        While using uinput backend, assign _position_getter
        """
        if self._position_getter is None:
            raise NotImplementedError("Position getter not assigned")

        return self._position_getter()

    def _position_set(self, pos):
        cur_x, cur_y = self._position_get()
        px, py = self._check_bounds(*pos)
        self._dev.write(ecodes.EV_REL, ecodes.REL_X, px-cur_x)
        self._dev.write(ecodes.EV_REL, ecodes.REL_Y, py-cur_y)
        self._dev.syn()

    def move(self, dx, dy):
        self._dev.write(ecodes.EV_REL, ecodes.REL_X, dx)
        self._dev.write(ecodes.EV_REL, ecodes.REL_Y, dy)
        self._dev.syn()

    def _scroll(self, dx, dy):
        dx, dy = self._check_bounds(dx, dy)
        if dy:
            self._dev.write(ecodes.EV_REL, ecodes.REL_WHEEL_HI_RES, dy)
        if dx:
            self._dev.write(ecodes.EV_REL, ecodes.REL_HWHEEL_HI_RES, dx)
        self._dev.syn()

    def _press(self, button: Button):
        self._dev.write(ecodes.EV_REL, button.value, 1)
        self._dev.syn()

    def _release(self, button):
        self._dev.write(ecodes.EV_REL, button.value, 0)
        self._dev.syn()

    def _check_bounds(self, *args):
        """Checks the arguments and makes sure they are within the bounds of a
        short integer.

        :param args: The values to verify.
        """
        if not all(
                (-0x7fff - 1) <= number <= 0x7fff
                for number in args):
            raise ValueError(args)
        else:
            return tuple(int(p) for p in args)


class Listener(ListenerMixin, _base.Listener):
    # current implementation only supports listening for mouse device
    # should be improved for supporting touchpad
    # Need to be improved with libinput
    _EVENTS = (
        ecodes.EV_KEY,
        ecodes.EV_REL,
        ecodes.EV_SYN)

    def __init__(self, *args, **kwargs):
        super(Listener, self).__init__(*args, **kwargs)

    def _get_device(self):
        device_path = None
        for path in evdev.list_devices():
            try:
                device = InputDevice(path)
            except OSError:
                continue
            capabilities = device.capabilities()
            # Check if the device contains left and right buttons
            # sort of a hack
            # May be improved later on
            if (all(event in capabilities.keys() for event in self._EVENTS)):
                if (ecodes.BTN_LEFT in capabilities[ecodes.EV_KEY] and
                   ecodes.BTN_RIGHT in capabilities[ecodes.EV_KEY] and
                   ecodes.REL_X in capabilities[ecodes.EV_REL] and
                   ecodes.REL_Y in capabilities[ecodes.EV_REL]):
                    device_path = path
                    device.close()
                    break
            
            device.close()

        if device_path is None:
            raise Exception("Could not find a valid mouse device")
        
        return InputDevice(device_path)

    def _handle(self, event: InputEvent):
        if event.type == ecodes.EV_KEY:
            self.on_click(self._button(event.code), event.value)

        elif event.type == ecodes.EV_REL:
            if (event.code == ecodes.REL_X):
                self.on_move(event.value, 0)
            elif (event.code == ecodes.REL_Y):
                self.on_move(0, event.value)
            elif (event.code == ecodes.REL_WHEEL_HI_RES):
                self.on_scroll(0, event.value)
            elif (event.code == ecodes.REL_HWHEEL_HI_RES):
                self.on_scroll(event.value, 0)

    # pylint: disable=R0201
    def _button(self, code):
        """Creates a mouse button from an event detail.

        If the button is unknown, :attr:`Button.unknown` is returned.

        :param detail: The event detail.

        :return: a button
        """
        try:
            return Button(code)
        except ValueError:
            return Button.unknown
    # pylint: enable=R0201
