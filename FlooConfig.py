import configparser
import os


class FlooConfig:

    def __init__(self):
        self.config = configparser.ConfigParser()
        self.load()

    def autoOn(self) -> bool:
        return self.config['DEFAULT'].getboolean('autoOn')

    def setAutoOn(self, auto_on):
        if auto_on:
            self.config['DEFAULT']['autoOn'] = 'yes'
        else:
            self.config['DEFAULT']['autoOn'] = 'no'
        self.save()

    def autoUrl(self) -> bool:
        return self.config['DEFAULT'].getboolean('autoUrl')

    def setAutoUrl(self, auto_on):
        if auto_on:
            self.config['DEFAULT']['autoUrl'] = 'yes'
        else:
            self.config['DEFAULT']['autoUrl'] = 'no'
        self.save()

    def notifOnImage(self) -> bool:
        return self.config['DEFAULT'].getboolean('notifOnImage')

    def setNotifOnImage(self, auto_on):
        if auto_on:
            self.config['DEFAULT']['notifOnImage'] = 'yes'
        else:
            self.config['DEFAULT']['notifOnImage'] = 'no'
        self.save()

    def shareToMobile(self) -> bool:
        return self.config['DEFAULT'].getboolean('shareToMobile')

    def setShareToMobile(self, auto_on):
        if auto_on:
            self.config['DEFAULT']['shareToMobile'] = 'yes'
        else:
            self.config['DEFAULT']['shareToMobile'] = 'no'
        self.save()

    def imageOpt(self):
        return int(self.config['DEFAULT']['imageOpt'])

    def setImageOpt(self, image_opt):
        self.config['DEFAULT']['imageOpt'] = str(image_opt)
        self.save()

    def load(self):
        if os.path.exists("FlooPaste.ini"):
            self.config.read("FlooPaste.ini")
        else:
            self.config['DEFAULT'] = {'autoOn': 'yes',
                                      'autoUrl': 'yes',
                                      'notifOnImage': 'yes',
                                      'shareToMobile': 'yes',
                                      'imageOpt': '0'}
        return self.config['DEFAULT']

    def save(self):
        with open('FlooPaste.ini', 'w') as configfile:
            self.config.write(configfile)
