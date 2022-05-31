# Import Module
import tkinter as tk
from tkinter import ttk
from pystray import MenuItem as TrayMenuItem
import pystray
from PIL import Image
import gettext
import serial.tools.list_ports
import webbrowser

# Search for COM port of FMA100
ports = [port.name for port in serial.tools.list_ports.grep('0A12:4007.*FMA100')]
if ports:
    comport = ports[0]
else:
    comport = "None"

# Set the local directory
localedir = './locale'
# Set up your magic function
translate = gettext.translation('appname', localedir, fallback=True)
_ = translate.gettext

# create root window
root = tk.Tk()

# root window title and dimension
root.title("FlooPaste")
# Set geometry (widthxheight)
root.geometry('485x300')

mainFrame = tk.Frame(root, relief=tk.RAISED)
mainFrame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

mainFrame.grid_rowconfigure(0, weight=1)
mainFrame.grid_columnconfigure(0, weight=1)
mainFrame.columnconfigure(0, weight=1)
mainFrame.columnconfigure(1, weight=1)
# Control panel
setupPanel = ttk.LabelFrame(mainFrame, text=_('Setup'))
setupPanel.grid(column=0, row=0, sticky='nsew')
# Window panel
windowPanel = ttk.LabelFrame(mainFrame, text=_('Window'))
windowPanel.grid(column=1, row=0, sticky='nsew')
# About panel
aboutPanel = ttk.LabelFrame(mainFrame, text=_('About'))
aboutPanel.grid(column=0, row=1, columnspan=2, sticky='nsew')

# setupPanel
setupPanel.grid_columnconfigure(0, weight=1)
setupPanel.columnconfigure(0, weight=1)
setupPanel.columnconfigure(1, weight=1)

# Define On/Off Images
on = tk.PhotoImage(file="onS.png")
off = tk.PhotoImage(file="offS.png")

# Start with Windows
# Label
autoStart = tk.Label(setupPanel, text=_("Start with Windows"))
autoStart.grid(column=0, row=0, sticky='w')
# SwitchButton
autoOn = True


# Define our switch function
def auto_on_switch():
    global autoOn
    # Determine is on or off
    if autoOn:
        autoUrlButton.config(image=off)
        autoOn = False
    else:
        autoUrlButton.config(image=on)
        autoOn = True


# Auto start with windows Button
autoOnButton = tk.Button(setupPanel, image=on, bd=0, command=auto_on_switch)
autoOnButton.grid(column=1, row=0, sticky='e')

# AutoOpenUrlLabel
autoUrlLabel = tk.Label(setupPanel, text=_("Auto open shared URL from the mobile app"))
autoUrlLabel.grid(column=0, row=1, sticky='w')

# AutoOpenUrlButton
autoUrlIsOn = True


# Define our switch function
def url_switch():
    global autoUrlIsOn
    # Determine is on or off
    if autoUrlIsOn:
        autoUrlButton.config(image=off)
        autoUrlIsOn = False
    else:
        autoUrlButton.config(image=on)
        autoUrlIsOn = True


# urlButton
autoUrlButton = tk.Button(setupPanel, image=on, bd=0, command=url_switch)
autoUrlButton.grid(column=1, row=1, sticky='e')

# compressionRatioLabel
compressionRatioLabel = tk.Label(setupPanel, text=_("Image quality when sharing from the PC"))
compressionRatioLabel.grid(column=0, row=2, sticky='w')
# compressionRatioSlider
compressRatio = tk.IntVar()
compressRatio.set(40)
compressionRationSlider = tk.Scale(setupPanel, from_=0, to=100, orient=tk.HORIZONTAL, variable=compressRatio)
compressionRationSlider.grid(column=0, row=3, columnspan=2, sticky='ew')


# Define our switch function
def reset_compress_ratio():
    compressRatio.set(40)


# Reset compression ration to default Button
compressRatioResetButton = tk.Button(setupPanel, text=_("Default"), command=reset_compress_ratio)
compressRatioResetButton.grid(column=1, row=4, sticky='ew', padx=(0, 3))


# aboutPanel
# Brand logo - FlooGoo
def url_callback(url):
    webbrowser.open_new(url)


supportLink = tk.Label(aboutPanel, text=_("Support Page"), fg="blue", cursor="hand2")
supportLink.pack()
supportLink.bind("<Button-1>", lambda e: url_callback("https://www.flairmesh.com/dongle/FMA100.html"))
versionInfo = tk.Label(aboutPanel, text="Version 1.0.0\nCopyright© 2022\nFlairmesh Technologies.")
versionInfo.pack()
# Support page

# status bar
if comport == "None":
    statusbar = tk.Label(root, text=_("Please insert your FMA100"), bd=1, relief=tk.SUNKEN, anchor=tk.W)
else:
    statusbar = tk.Label(root, text=_("Use FMA100 on " + comport), bd=1, relief=tk.SUNKEN, anchor=tk.W)
    # webbrowser.open('https://www.google.com')
# statusbar.grid(column = 0, row = 2)
statusbar.pack(side=tk.BOTTOM, fill=tk.X)


def quit_all():
    root.destroy()


# Define a function for quit the window
def quit_window(icon, TrayMenuItem):
    icon.stop()
    root.destroy()


# Define a function to show the window again
def show_window(icon, TrayMenuItem):
    icon.stop()
    root.after(0, root.deiconify())


# Hide the window and show on the system taskbar
def hide_window():
    root.withdraw()
    image = Image.open("FlooPaste.ico")
    menu = (TrayMenuItem(_('Quit'), quit_window), TrayMenuItem(_('Show'), show_window))
    icon = pystray.Icon("FlooPaste", image, _("FlooGoo Paste Board"), menu)
    icon.run()


root.protocol('WM_DELETE_WINDOW', hide_window)

# WindowPanel
# windowPanel.grid_rowconfigure(0, weight=1)
windowPanel.grid_columnconfigure(0, weight=1)
windowPanel.grid_columnconfigure(1, weight=1)
windowPanel.columnconfigure(0, weight=1)
windowPanel.columnconfigure(1, weight=1)
# portOnButton
portIsOn = True


# Define our switch function
def port_switch():
    global portIsOn
    # Determine is on or off
    if portIsOn:
        portOnButton.config(image=off)
        portIsOn = False
    else:
        portOnButton.config(image=on)
        portIsOn = True


# portOnLabel
portOnLabel = tk.Label(windowPanel, text=_("Running Status"))
portOnLabel.grid(column=0, row=0, sticky='w')
portOnButton = tk.Button(windowPanel, image=on, bd=0, command=port_switch)
portOnButton.grid(column=1, row=0, sticky='e')
minimizeButton = tk.Button(windowPanel, text=_("Minimize to System Tray"), command=hide_window)
minimizeButton.grid(column=0, row=1, columnspan=2, padx=(10, 10), pady=(10, 10), sticky='ew')
quitButton = tk.Button(windowPanel, text=_("Quit App"), command=quit_all)
quitButton.grid(column=0, row=2, columnspan=2, padx=(10, 10), pady=(0, 10), sticky='ew')

# all widgets will be here
# Execute Tkinter
root.mainloop()
