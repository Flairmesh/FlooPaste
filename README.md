# FlooPaste

A python application allows copying & pasting between a host and an iOS device.

It requires a FlooGoo FMA100 Bluetooth dongle inserted to a USB port on the host and the iOS app "FlooPaste" running on the iOS device.

- On Windows, it supports copying&pasting text&URL&image.
- On Linux, now it only supports text.

## Installation

On Windows, the compiled App can be downloaded directly from Microsoft Store.

Requires python 3.7+
Please also install the following modules when needed.

notify-py
tkinter
Pillow
pyclip (needs xclip or wl-clipboard)
pyserial
pystray
validators
 
## Usage

Keep the app running on the host and the iOS app "FlooPaste" running on the iOS device.
 
## Platform specific notes/issues

### Linux

There're some issues when the app is minimized to an icon in the system tray, so please only minimize the window.

Linux on X11 requires `xclip` to work. Install with your package manager, e.g. `sudo apt install xclip`
Linux on Wayland requires `wl-clipboard` to work. Install with your package manager, e.g. `sudo apt install wl-clipboard`

# Acknowledgements

