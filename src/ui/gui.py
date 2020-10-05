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

import util.image_psnr
from datetime import date
from controller import StegoAudio, StegoImage, StegoImageBPCS, StegoVideo
from controller.audio_controller import psnr


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        loadUi(os.getcwd() + '/ui/main.ui', self)
        self.setupUI()
        self.stegoAudio = None
        self.stegoImageLSB = None
        self.stegoImageBPCS = None
        self.stegoVideo = None

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
        self.imgFileInpPathBtn.clicked.connect(self.imageSelectFileInput)
        self.imgHideFileBtn.clicked.connect(self.imageExecHideFile)
        self.imgSaveOutBtn.clicked.connect(self.saveStegoImage)
        self.imgMethUsedInp.addItems(["LSB", "BPCS"])
        # image extract
        self.backImagePageNavBtnE.clicked.connect(self.image)
        self.imgStegPathInpE.returnPressed.connect(self.imageInputPathChanged)
        self.imgStegPathBtnE.clicked.connect(self.selectImageInput)
        self.imgExtractButton.clicked.connect(self.imageExecExtractFile)
        self.imgSaveOutButtonE.clicked.connect(self.imageSaveOutfile)
        self.imgMethUsedInpE.addItems(["LSB", "BPCS"])
        # audio menu
        self.AHidePageButton.clicked.connect(self.audioHide)
        self.AExtractPageButton.clicked.connect(self.audioExtract)
        self.AAudioBackPageButton.clicked.connect(self.mainMenu)
        # audio hide
        self.AHideButton.clicked.connect(self.audioHideFile)
        self.ABackToAudioButtonH.clicked.connect(self.audio)
        self.ASaveAudioH.hide()
        self.APlayAudioH.hide()
        self.PSNRLabelRes.hide()
        self.audioPathFileDialogH.clicked.connect(self.audioInputPathChanged)
        self.filePathFileDialogH.clicked.connect(self.fileInputPathChanged)
        # audio extract
        self.AExtractButton.clicked.connect(self.audioExtract)
        

    def mainMenu(self):
        self.stackedWidget.setCurrentIndex(0)

    # image
    def image(self):
        if self.stackedWidget.currentIndex() == 2:
            # image
            self.imageRawPicLabel.clear()
            self.imageStegoPicLabel.clear()
            # path input
            self.imgRawPathInp.clear()
            self.imgFileInpPathInp.clear()
            # key and others
            self.imgKeyInp.clear()
            self.imgEncInp.setChecked(False)
            self.imgNonSeqInp.setChecked(False)
        elif self.stackedWidget.currentIndex() == 3:
            # image
            self.imageInpPicLabelE.clear()
            # path input
            self.imgStegPathInpE.clear()
            self.imgFileOutPathInpE.clear()
            # key and others
            self.imgKeyInpE.clear()
            self.imgEncInpE.setChecked(False)
        # delete image controller
        self.stegoImageLSB = None
        self.stegoImageBPCS = None
        self.stackedWidget.setCurrentIndex(1)

    def imageHide(self):
        self.stackedWidget.setCurrentIndex(2)

    def imageExtract(self):
        self.stackedWidget.setCurrentIndex(3)

    # IMAGE HELPER
    def getStegoImage(self):
        if self.stackedWidget.currentIndex() == 2:
            print(self.imgMethUsedInp.currentText())
            if self.imgMethUsedInp.currentText() == "LSB":
                return self.stegoImageLSB
            elif self.imgMethUsedInp.currentText() == "BPCS":
                return self.stegoImageBPCS
        elif self.stackedWidget.currentIndex() == 3:
            print(self.imgMethUsedInpE.currentText())
            if self.imgMethUsedInpE.currentText() == "LSB":
                return self.stegoImageLSB
            elif self.imgMethUsedInpE.currentText() == "BPCS":
                return self.stegoImageBPCS
        return None

    # IMAGE HIDE
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
        self.stegoImageLSB = StegoImage(fileName)
        self.stegoImageBPCS = StegoImageBPCS(fileName)
        if self.stackedWidget.currentIndex() == 2:
            picLabel = self.imageRawPicLabel
            pathInp = self.imgRawPathInp
        elif self.stackedWidget.currentIndex() == 3:
            picLabel = self.imageInpPicLabelE
            pathInp = self.imgStegPathInpE
        else:
            print('Error occured')
            return
        qim = ImageQt(self.stegoImageLSB.image)
        pixmap = QPixmap.fromImage(qim)
        pixmap = pixmap.scaled(picLabel.width(), picLabel.height(), QtCore.Qt.KeepAspectRatio)
        picLabel.setPixmap(pixmap)
        picLabel.setAlignment(QtCore.Qt.AlignCenter)
        pathInp.setText(fileName)

    # exec hide img
    def imageSelectFileInput(self):
        fileName, _ = QFileDialog.getOpenFileName(None, "Select File", "", "All (*)")
        self.imgFileInpPathInp.setText(fileName)

    def imageExecHideFile(self):
        stegoImage = self.getStegoImage()
        if stegoImage is None:
            self.dialogWindow("Invalid Action", "Please add raw image first", subtext="", type="Warning")
            return
        in_filename = self.imgFileInpPathInp.text()
        encryption = self.imgEncInp.isChecked()
        is_sequential = not self.imgNonSeqInp.isChecked()
        key = self.imgKeyInp.text()
        if (encryption or not is_sequential) and not key:
            self.dialogWindow("Invalid Action", "Please input key when using non sequential or encryption", subtext="", type="Warning")
            return
        stegoImage.insert_data(in_filename, is_sequential, key)
        self.setImageOutput(stegoImage)

    def setImageOutput(self, stegoImage):
        picLabel = self.imageStegoPicLabel
        qim = ImageQt(self.stegoImageLSB.stego_image)
        pixmap = QPixmap.fromImage(qim)
        pixmap = pixmap.scaled(picLabel.width(), picLabel.height(), QtCore.Qt.KeepAspectRatio)
        picLabel.setPixmap(pixmap)
        picLabel.setAlignment(QtCore.Qt.AlignCenter)

    # save steg image
    def saveStegoImage(self):
        stegoImage = self.getStegoImage()
        if stegoImage is None:
            self.dialogWindow("Invalid Action", "Please add raw image first", subtext="", type="Warning")
            return
        if stegoImage.stego_image is None:
            self.dialogWindow("Invalid Action", "Please hide file first", subtext="", type="Warning")
            return
        fileName, _ = QFileDialog.getSaveFileName(None, "Save Stego Image", "", "All (*)")
        stegoImage.save_stego_image(fileName)

    # IMAGE EXTRACT
    # exec extract file
    def imageExecExtractFile(self):
        stegoImage = self.getStegoImage()
        if stegoImage is None:
            self.dialogWindow("Invalid Action", "Please add stego image first", subtext="", type="Warning")
            return
        key = self.imgKeyInpE.text()
        if encryption and not key:
            self.dialogWindow("Invalid Action", "Please input key when using encryption", subtext="", type="Warning")
            return
        if not key:
            key = '1337'  # default non sequential extract key
        stegoImage.extract_data(key)

    # save extracted file
    def imageSaveOutfile(self):
        stegoImage = self.getStegoImage()
        if stegoImage is None:
            self.dialogWindow("Invalid Action", "Please add stego image first", subtext="", type="Warning")
            return
        if stegoImage.stego_image is None:
            self.dialogWindow("Invalid Action", "Please extract message first", subtext="", type="Warning")
            return
        defaultFilename = stegoImage.extracted_filename
        fileName, _ = QFileDialog.getSaveFileName(None, "Save Extracted File", defaultFilename, "All (*)")
        stegoImage.save_extracted_data(fileName)

    # audio
    def audio(self):
        # pindah ke page menu audio
        self.stackedWidget.setCurrentIndex(4)

    def audioHide(self):
        # pindah ke page hide
        self.stackedWidget.setCurrentIndex(5)

    def audioHideFile(self):
        # tombol hide file
        audio_path = self.audioTextEditH.toPlainText()
        file_path = self.fileTextEditH.toPlainText()
        key = self.keyTextEditH.toPlainText()
        self.hideAudio = StegoAudio(key, audio_path)
        self.stegoAudio.insert_data(file_path, self.ASeqCheck.isChecked())
        self.ASaveAudioH.show()
        self.APlayAudioH.show()
        self.ASaveAudioH.clicked.connect(self.saveAudio)
        self.APlayAudioH.clicked.connect(self.playAudio)
        # hide.save_stego_audio("example/lol.wav")
        # extractor = StegoAudio(key, "example/lol.wav")
        # extractor.extract_data()
        # extractor.save_extracted_file("example/lala.pdf")
        # psnr("example/test.wav", "example/lol.wav")
        # print(file_path)
    
    def saveAudio(self):
        audio_res = self.
        self.stegoAudio.save_stego_audio()

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
