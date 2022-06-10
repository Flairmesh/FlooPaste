# Import Module
import sys
import locale
import tkinter as tk
from tkinter import ttk
from pystray import MenuItem as TrayMenuItem
import pystray
from PIL import Image
import gettext
import webbrowser
from FlooTransceiver import FlooTransceiver
from FlooPacket import FlooPacket
import Startup
import FlooConfig


userLocale = locale.getdefaultlocale()
lan = userLocale[0].split('_')[0]
# print(lan)

# Set the local directory
localedir = './locale'
# Set up your magic function
translate = gettext.translation("messages", localedir, languages=[lan], fallback=True)
translate.install()
_ = translate.gettext

# create root window
root = tk.Tk()

# Create Startup bat
Startup.add_to_startup()

flooConfig = FlooConfig.FlooConfig()

autoOn = flooConfig.autoOn()
autoUrl = flooConfig.autoUrl()
notifOnImage = flooConfig.notifOnImage()
shareToMobile = flooConfig.shareToMobile()
# print("auto on", autoOn, "autoUrl", autoUrl)
imageOpt = tk.IntVar()
imageOpt.set(flooConfig.imageOpt())

# root window title and dimension
root.title("FlooPaste")
root.iconbitmap('FlooPasteApp.ico')
# root.iconphoto(False, tk.PhotoImage(file='FlooPasteIcon.png'))
# Set geometry (widthxheight)
root.geometry('485x300')

mainFrame = tk.Frame(root, relief=tk.RAISED)
mainFrame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

mainFrame.rowconfigure(0, weight=2)
# mainFrame.rowconfigure(1, weight=1)
# mainFrame.grid_columnconfigure(0, weight=1)
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
# setupPanel.grid_columnconfigure(0, weight=1)
setupPanel.columnconfigure(0, weight=1)
setupPanel.columnconfigure(1, weight=1)
setupPanel.columnconfigure(2, weight=1)

# Define On/Off Images
on = tk.PhotoImage(file="onS.png")
off = tk.PhotoImage(file="offS.png")

# Start with Windows
# Label
autoStart = tk.Label(setupPanel, text=_("Start when logged into Windows"))
autoStart.grid(column=0, row=0, sticky='w')
# SwitchButton


# Define our switch function
def auto_on_switch():
    global autoOn
    # Determine is on or off
    if autoOn:
        autoOnButton.config(image=off)
        autoOn = False
        Startup.remove_from_startup()
    else:
        autoOnButton.config(image=on)
        autoOn = True
        Startup.add_to_startup()
    flooConfig.setAutoOn(autoOn)


# Auto start with windows Button
if autoOn:
    autoOnButton = tk.Button(setupPanel, image=on, bd=0, command=auto_on_switch)
    Startup.add_to_startup()
else:
    autoOnButton = tk.Button(setupPanel, image=off, bd=0, command=auto_on_switch)
    Startup.remove_from_startup()
autoOnButton.grid(column=2, row=0, sticky='e')

# Initialize FlooTransceiver
notifText = _("New image pasted")
if notifOnImage:
    floo_transceiver = FlooTransceiver(autoUrl, imageOpt.get(), shareToMobile, notifText)
else:
    floo_transceiver = FlooTransceiver(autoUrl, imageOpt.get(), shareToMobile, None)
floo_transceiver.daemon = True

# shareToMobile Switch
# portOnLabel
shareToMobileLabel = tk.Label(setupPanel, text=_("Share to Mobile"))
shareToMobileLabel.grid(column=0, row=1, sticky='w')


# Define our switch function
def share_to_mobile_switch():
    global shareToMobile
    # Determine is on or off
    if shareToMobile:
        shareToMobileButton.config(image=off)
        shareToMobile = False
    else:
        shareToMobileButton.config(image=on)
        shareToMobile = True
    floo_transceiver.setShareToMobile(shareToMobile)
    flooConfig.setShareToMobile(shareToMobile)


if shareToMobile:
    shareToMobileButton = tk.Button(setupPanel, image=on, bd=0, command=share_to_mobile_switch)
else:
    shareToMobileButton = tk.Button(setupPanel, image=off, bd=0, command=share_to_mobile_switch)
shareToMobileButton.grid(column=2, row=1, sticky='e')

# AutoOpenUrlLabel
autoUrlLabel = tk.Label(setupPanel, text=_("Auto open shared URL from Mobile"))
autoUrlLabel.grid(column=0, row=2, sticky='w')


# Define our switch function
def url_switch():
    global autoUrl
    # Determine is on or off
    if autoUrl:
        autoUrlButton.config(image=off)
        autoUrl = False
    else:
        autoUrlButton.config(image=on)
        autoUrl = True
    floo_transceiver.setAutoUrl(autoUrl)
    flooConfig.setAutoUrl(autoUrl)


# Auto open URL from mobile
if autoUrl:
    autoUrlButton = tk.Button(setupPanel, image=on, bd=0, command=url_switch)
else:
    autoUrlButton = tk.Button(setupPanel, image=off, bd=0, command=url_switch)
autoUrlButton.grid(column=2, row=2, sticky='e')


# Send a notification when an image is got
notifOnImageLabel = tk.Label(setupPanel, text=_("Notification upon receiving image"))
notifOnImageLabel.grid(column=0, row=3, sticky='w')


# Define our switch function
def notif_on_image_switch():
    global notifOnImage
    global notifText
    # Determine is on or off
    if notifOnImage:
        notifOnImageButton.config(image=off)
        notifOnImage = False
        floo_transceiver.setNotifOnImage(None)
    else:
        notifOnImageButton.config(image=on)
        notifOnImage = True
        floo_transceiver.setNotifOnImage(notifText)
    flooConfig.setNotifOnImage(notifOnImage)


if notifOnImage:
    notifOnImageButton = tk.Button(setupPanel, image=on, bd=0, command=notif_on_image_switch)
else:
    notifOnImageButton = tk.Button(setupPanel, image=off, bd=0, command=notif_on_image_switch)
notifOnImageButton.grid(column=2, row=3, sticky='e')


# imageOptimizationRatioLabel
imageOptimizationRatioLabel = tk.Label(setupPanel, text=_("Image optimization when sharing from PC"))
imageOptimizationRatioLabel.grid(column=0, row=4, sticky='w')

imageOptRadioFrame = tk.Frame(setupPanel, relief=tk.RAISED)
imageOptRadioFrame.grid(column=0, row=5, columnspan=3, sticky='ew')

# imageOptimizationRatio


def imageOptSel():
    floo_transceiver.setImageOpt(imageOpt.get())
    flooConfig.setImageOpt(imageOpt.get())


R1 = tk.Radiobutton(imageOptRadioFrame, text=_("Fast Transfer"), variable=imageOpt, value=0, command=imageOptSel)
R1.grid(column=0, row=0, sticky='w')
R2 = tk.Radiobutton(imageOptRadioFrame, text=_("Balanced"), variable=imageOpt, value=1, command=imageOptSel)
R2.grid(column=1, row=0, sticky='w')
R3 = tk.Radiobutton(imageOptRadioFrame, text=_("Quality"), variable=imageOpt, value=2, command=imageOptSel)
R3.grid(column=2, row=0, sticky='w')


# aboutPanel
# Brand logo - FlooGoo
def url_callback(url):
    webbrowser.open_new(url)


aboutPanel.columnconfigure(0, weight=1)
aboutPanel.columnconfigure(1, weight=1)

aboutFrame = tk.Frame(aboutPanel, relief=tk.RAISED)
aboutFrame.grid(column=1, row=0, sticky='nsew')

versionInfo = tk.Label(aboutFrame, text=_("Version") + "1.0.0")
versionInfo.pack()

supportLink = tk.Label(aboutFrame, text=_("Support Link"), fg="blue", cursor="hand2")
supportLink.pack()
supportLink.bind("<Button-1>", lambda e: url_callback("https://www.flairmesh.com/dongle/FMA100.html"))

thirdPartyLink = tk.Label(aboutFrame, text=_("Third-Party Software Licenses"), fg="blue", cursor="hand2")
thirdPartyLink.pack()
thirdPartyLink.bind("<Button-1>", lambda e: url_callback("https://www.flairmesh.com/support/third_lic.html"))

copyRightInfo = tk.Label(aboutFrame, text="Copyright© 2022 Flairmesh Technologies.")
copyRightInfo.pack()

logoFrame = tk.Frame(aboutPanel, relief=tk.RAISED)
logoFrame.grid(column=0, row=0, sticky='nsew')
logo = tk.Canvas(logoFrame, width=230, height=64)
img = tk.PhotoImage(file="FlooPasteHeader.png")
logo.create_image(0, 0, anchor=tk.NW, image=img)
logo.pack()

# Support page

# statusbar.grid(column = 0, row = 2)
statusbar = tk.Label(root, text=_("Initializing"), bd=1, relief=tk.SUNKEN, anchor=tk.W)
statusbar.pack(side=tk.BOTTOM, fill=tk.X)

windowIcon = None


def quit_all():
    root.destroy()


# Define a function for quit the window
def quit_window(icon, TrayMenuItem):
    icon.stop()
    root.destroy()


# Define a function to show the window again
def show_window(icon, TrayMenuItem):
    global windowIcon
    icon.stop()
    root.after(0, root.deiconify())
    windowIcon = None


# Hide the window and show on the system taskbar
def hide_window():
    global windowIcon
    root.withdraw()
    image = Image.open("FlooPasteApp.ico")
    menu = (TrayMenuItem(_('Quit'), quit_window), TrayMenuItem(_('Show Window'), show_window))
    icon = pystray.Icon("FlooPaste", image, _("FlooGoo Paste Board"), menu)
    icon.run()
    windowIcon = icon


root.protocol('WM_DELETE_WINDOW', hide_window)

# WindowPanel
windowPanel.columnconfigure(0, weight=1)
windowPanel.columnconfigure(1, weight=1)

minimizeButton = tk.Button(windowPanel, text=_("Minimize to System Tray"), command=hide_window)
minimizeButton.grid(column=0, row=0, columnspan=2, padx=(10, 10), pady=(10, 10), sticky='ew')
quitButton = tk.Button(windowPanel, text=_("Quit App"), command=quit_all)
quitButton.grid(column=0, row=1, columnspan=2, padx=(10, 10), pady=(0, 10), sticky='ew')

floo_transceiver.start()


def heartbeat_task():
    global statusbar
    global floo_transceiver
    global windowIcon
    port_name = floo_transceiver.port_name
    # status bar
    if floo_transceiver.port is None:
        statusbar.config(text=_("Please insert your FlooGoo dongle"))
    else:
        # check local clipboard
        if floo_transceiver.notified == FlooPacket.TYP_STR:
            statusbar.config(
                text=_("Use FlooGoo dongle on ") + port_name + " - " + _("A new string pasted from your mobile App"))
        elif floo_transceiver.notified == FlooPacket.TYP_IMG:
            statusbar.config(
                text=_("Use FlooGoo dongle on ") + port_name + " - " + _("A new image pasted from your mobile App"))
        else:
            statusbar.config(
                text=_("Use FlooGoo dongle on ") + port_name)

    root.after(1000, heartbeat_task)  # reschedule event in 2 seconds


# Start transceiver to FlooGoo
root.after(1000, heartbeat_task)

if len(sys.argv) > 1:
    hide_window()

# all widgets will be here
# Execute Tkinter
root.mainloop()
