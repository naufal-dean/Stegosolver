import os
import sqlite3
import time
from PIL.ImageQt import ImageQt
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.uic import loadUi
from PyQt5.Qt import QAbstractItemView
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from datetime import date
from controller import StegoImage, StegoAudio
from controller.audio_controller import psnr


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        loadUi(os.getcwd() + '/ui/main.ui', self)
        self.setupUI()

    def setupUI(self):
        self.stackedWidget.setCurrentIndex(0)
        # main menu
        self.imageButton.clicked.connect(self.image)
        self.audioButton.clicked.connect(self.audio)
        # image menu
        self.imageHideNavBtn.clicked.connect(self.imageHide)
        self.imageExtractNavBtn.clicked.connect(self.imageExtract)
        self.imageBackMainMenuNavBtn.clicked.connect(self.mainMenu)
        # image hide
        self.backImagePageNavBtn.clicked.connect(self.image)
        self.imgRawPathInp.returnPressed.connect(self.imageInputPathChanged)
        self.imgRawPathBtn.clicked.connect(self.selectImageInput)
        # image extract
        self.backImagePageNavBtnE.clicked.connect(self.image)
        # audio menu
        self.AHidePageButton.clicked.connect(self.audioHide)
        self.AHideButton.clicked.connect(self.audioHideFile)

    def mainMenu(self):
        self.stackedWidget.setCurrentIndex(0)

    # image
    def image(self):
        self.stackedWidget.setCurrentIndex(1)

    def imageHide(self):
        self.stackedWidget.setCurrentIndex(2)

    def imageExtract(self):
        self.stackedWidget.setCurrentIndex(3)

    # image input
    def selectImageInput(self):
        fileName, _ = QFileDialog.getOpenFileName(None, "Select Image", "", "Image Files (*.png *.bmp)")
        if fileName:
            self.setImageInput(fileName)

    def imageInputPathChanged(self):
        try:    # test file existence
            if os.path.isfile(self.imgRawPathInp.text()):  # image test
                self.setImageInput(self.imgRawPathInp.text())
            else:
                self.dialogWindow("Open File", self.imgRawPathInp.text(), subtext="File not found!", type="Warning")
        except IOError:
            self.dialogWindow("Open File", self.imgRawPathInp.text(), subtext="File is not an image!", type="Warning")

    def setImageInput(self, fileName):
        self.stegoImage = StegoImage(fileName)
        qim = ImageQt(self.stegoImage.image)
        pixmap = QPixmap.fromImage(qim)
        pixmap = pixmap.scaled(self.imageStegoPicLabel.width(), self.imageStegoPicLabel.height(), QtCore.Qt.KeepAspectRatio)
        self.imageStegoPicLabel.setPixmap(pixmap)
        self.imageStegoPicLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.imgRawPathInp.setText(fileName)

    # audio
    def audio(self):
        self.stackedWidget.setCurrentIndex(4)

    def audioHide(self):
        self.stackedWidget.setCurrentIndex(5)

    def audioHideFile(self):
        audio_path = self.audioTextEdit.toPlainText()
        file_path = self.fileTextEdit.toPlainText()
        key = self.keyTextEdit.toPlainText()
        hide = StegoAudio(key, audio_path)
        hide.insert_data(file_path, self.ASeqCheck.isChecked())
        hide.save_stego_audio("example/lol.wav")
        extractor = StegoAudio(key, "example/lol.wav")
        extractor.extract_data()
        extractor.save_extracted_file("example/lala.pdf")
        psnr("example/test.wav", "example/lol.wav")
        print(file_path)

    # dialog window helper
    def dialogWindow(self, title, text, subtext="" , type="Information"):
        message = QMessageBox()
        if type == "Question":
            message.setIcon(QMessageBox.Question)
        elif type == "Warning":
            message.setIcon(QMessageBox.Warning)
        elif type == "Critical":
            message.setIcon(QMessageBox.Critical)
        else:
            message.setIcon(QMessageBox.Information)
        message.setWindowTitle(title)
        message.setWindowIcon(QIcon("icon/qmessage_icon.png"))
        message.setText(text)
        message.setInformativeText(subtext)
        message.setStandardButtons(QMessageBox.Ok)
        message.exec()
