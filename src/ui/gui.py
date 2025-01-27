import numpy as np
import os
import sqlite3
import time
import subprocess
from PIL.ImageQt import ImageQt
from PyQt5 import QtCore, QtGui, QtWidgets, QtMultimedia

from PyQt5.uic import loadUi
from PyQt5.Qt import QAbstractItemView
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

import util.image_psnr, util.audio_psnr
from datetime import date
from controller import StegoAudio, StegoImage, StegoImageBPCS, StegoVideo


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
        self.videoButton.clicked.connect(self.video)
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
        self.APSNRLabelRes.hide()
        self.APSNRLabel.hide()
        self.APathFileDialogH.clicked.connect(self.selectAudioInput)
        self.AFilePathFileDialogH.clicked.connect(self.selectMessageInput)
        # self.APathFileDialogH.clicked.connect(self.audioInputPathChanged)
        # self.AFilePathFileDialogH.clicked.connect(self.fileInputPathChanged)
        # audio extract
        self.AExtractButton.clicked.connect(self.audioExtractFile)
        self.ASaveMessage.hide()
        self.AErrMsg.hide()
        self.AFilePathFileDialogE.clicked.connect(self.selectAudioExtractInput)

        # video menu
        self.VHidePageButton.clicked.connect(self.videoHide)
        self.VExtractPageButton.clicked.connect(self.videoExtract)
        # self.VVideoBackPageButton.clicked.connect(self.mainMenu)
        # video hide
        self.VHideButtonH.clicked.connect(self.videoHideFile)
        self.VBackToVideoButtonH.clicked.connect(self.video)
        self.VSaveVideoH.hide()
        self.VPlayVideoH.hide()
        self.VPathFileDialogH.clicked.connect(self.selectVideoInput)
        self.VFilePathFileDialogH.clicked.connect(self.selectVideoMessageInput)
        # self.APathFileDialogH.clicked.connect(self.audioInputPathChanged)
        # self.AFilePathFileDialogH.clicked.connect(self.fileInputPathChanged)
        # audio extract
        self.VExtractButton.clicked.connect(self.videoExtractFile)
        self.VSaveMessage.hide()
        self.VPlayVideoE.hide()
        self.VFilePathFileDialogE.clicked.connect(self.selectVideoExtractInput)


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
            self.imgPSNRvalueLbl.clear()
        elif self.stackedWidget.currentIndex() == 3:
            # image
            self.imageInpPicLabelE.clear()
            # path input
            self.imgStegPathInpE.clear()
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
        try:
            stegoImage.insert_data(in_filename, encryption, is_sequential, key)
            self.setImageOutput(stegoImage)
        except Exception as e:
            self.dialogWindow("Error Happened", str(e), subtext="", type="Warning")
        else:
            self.dialogWindow("Succeed Inserting Message", "To save the stego image, click 'Save Output'", subtext="", type="Information")
            try:
                image_data_1 = np.array(stegoImage.image)
                image_data_2 = np.array(stegoImage.stego_image)
                if self.imgMethUsedInp.currentText() == "LSB":
                    psnr = str(util.image_psnr.psnr(image_data_1, image_data_2))
                elif self.imgMethUsedInp.currentText() == "BPCS":
                    image_data_1 = stegoImage.pad_image(image_data_1)
                    psnr = str(util.image_psnr.psnr(image_data_1, image_data_2))
                else:
                    psnr = ""
                self.imgPSNRvalueLbl.setText(psnr)
            except Exception as e:
                print(e)

    def setImageOutput(self, stegoImage):
        picLabel = self.imageStegoPicLabel
        qim = ImageQt(stegoImage.stego_image)
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
        fileName, _ = QFileDialog.getSaveFileName(None, "Save Stego Image", "", "Image Files (*.png *.bmp)")
        if not fileName:
            return
        try:
            stegoImage.save_stego_image(fileName)
        except Exception as e:
            self.dialogWindow("Invalid Filename Extension", "Cannot save image with name: " + fileName, subtext="Please use .png or .bmp extension", type="Warning")

    # IMAGE EXTRACT
    # exec extract file
    def imageExecExtractFile(self):
        stegoImage = self.getStegoImage()
        if stegoImage is None:
            self.dialogWindow("Invalid Action", "Please add stego image first", subtext="", type="Warning")
            return
        encryption = self.imgEncInpE.isChecked()
        key = self.imgKeyInpE.text()
        if encryption and not key:
            self.dialogWindow("Invalid Action", "Please input key when using encryption", subtext="", type="Warning")
            return
        if not key:
            key = '1337'  # default non sequential extract key
        print(key)
        try:
            stegoImage.extract_data(encryption, key)
        except Exception as e:
            self.dialogWindow("Error Happened", str(e), subtext="", type="Warning")
        else:
            self.dialogWindow("Succeed Extracting Message", "To save the message, click 'Save Output'", subtext="", type="Information")

    # save extracted file
    def imageSaveOutfile(self):
        stegoImage = self.getStegoImage()
        if stegoImage is None:
            self.dialogWindow("Invalid Action", "Please add stego image first", subtext="", type="Warning")
            return
        if stegoImage.extracted_data is None:
            self.dialogWindow("Invalid Action", "Please extract message first", subtext="", type="Warning")
            return
        defaultFilename = stegoImage.extracted_filename
        fileName, _ = QFileDialog.getSaveFileName(None, "Save Extracted File", defaultFilename, "All (*)")
        if not fileName:
            return
        try:
            stegoImage.save_extracted_data(fileName)
        except Exception as e:
            self.dialogWindow("Error Happened", str(e), subtext="", type="Warning")

    # audio
    def audio(self):
        # pindah ke page menu audio
        self.stackedWidget.setCurrentIndex(4)
        self.AKeyTextEditH.setText("")
        self.AKeyTextEditE.setText("")
        self.APathTextEditH.setText("")
        self.AFileTextEditH.setText("")
        self.APathTextEditE.setText("")

    def selectAudioInput(self):
        fileName, _ = QFileDialog.getOpenFileName(None, "Select Audio", "", "Audio Files (*.wav)")
        if fileName:
            self.APathTextEditH.setText(fileName)

    def selectAudioExtractInput(self):
        fileName, _ = QFileDialog.getOpenFileName(None, "Select Audio", "", "Audio Files (*.wav)")
        if fileName:
            self.APathTextEditE.setText(fileName)

    def selectMessageInput(self):
        fileName, _ = QFileDialog.getOpenFileName(None, "Select Message File", "", "All (*)")
        if fileName:
            self.AFileTextEditH.setText(fileName)

    def audioExtract(self):
        # pindah ke page extract
        self.stackedWidget.setCurrentIndex(6)

    def audioExtractFile(self):
        # tombol extract file
        self.audio_path_input = self.APathTextEditE.toPlainText()
        key = self.AKeyTextEditE.toPlainText()
        try:
            self.stegoAudio = StegoAudio(key, self.audio_path_input)
            self.AErrMsg.hide()
            self.stegoAudio.extract_data()
            self.ASaveMessage.show()
            self.APlayAudioE.show()
            self.ASaveMessage.clicked.connect(self.saveMessageFromAudio)
        except:
            self.AErrMsg.setText("audio path not exist")
            self.AErrMsg.show()

    def saveMessageFromAudio(self):
        fileName, _ = QFileDialog.getSaveFileName(None, "Save Message Stego Audio", self.stegoAudio.filename, "All (*)")
        self.stegoAudio.save_extracted_file(fileName)

    def audioHide(self):
        # pindah ke page hide
        self.stackedWidget.setCurrentIndex(5)

    def audioHideFile(self):
        # tombol hide file
        self.audio_path_input = self.APathTextEditH.toPlainText()
        file_path = self.AFileTextEditH.toPlainText()
        key = self.AKeyTextEditH.toPlainText()
        if key == '':
            self.AKeyTextEditH.setText("please fill the key")
        else:
            try:
                self.stegoAudio = StegoAudio(key, self.audio_path_input)
                self.APSNRLabelRes.hide()
                self.stegoAudio.insert_data(file_path, not self.ASeqCheck.isChecked(), key)
                self.ASaveAudioH.show()
                self.ASaveAudioH.clicked.connect(self.saveAudio)
            except:
                self.APSNRLabelRes.setText("message/audio path not exist")
                self.APSNRLabelRes.show()

    def saveAudio(self):
        self.fileName_audio_save, _ = QFileDialog.getSaveFileName(None, "Save Stego Audio", self.stegoAudio.audio_filename, "Audio Files (*.wav)")
        self.stegoAudio.save_stego_audio(self.fileName_audio_save)
        psnr = util.audio_psnr.psnr(self.audio_path_input, self.fileName_audio_save)
        self.APSNRLabelRes.setText(str(psnr))
        self.APSNRLabelRes.show()
        self.APSNRLabel.show()
        self.APlayAudioH.show()
        self.APlayAudioH.clicked.connect(self.playAudio)

    def playAudio(self):
        print("lala")
        subprocess.call(["ffplay", self.fileName_audio_save], stdout=open(os.devnull, "w"), stderr=subprocess.STDOUT)

        # url = QtCore.QUrl.fromLocalFile(self.fileName_audio_save)
        # content = QtMultimedia.QMediaContent(url)
        # player = QtMultimedia.QMediaPlayer()
        # player.setMedia(content)
        # player.setVolume(50.0)
        # player.play()

    def video(self):
        # pindah ke page menu video
        self.stackedWidget.setCurrentIndex(9)

    def selectVideoInput(self):
        fileName, _ = QFileDialog.getOpenFileName(None, "Select Video", "", "Video Files (*.avi)")
        if fileName:
            self.VPathTextEditH.setText(fileName)

    def selectVideoExtractInput(self):
        fileName, _ = QFileDialog.getOpenFileName(None, "Select Video", "", "Video Files (*.avi)")
        if fileName:
            self.VPathTextEditE.setText(fileName)

    def selectVideoMessageInput(self):
        fileName, _ = QFileDialog.getOpenFileName(None, "Select Message File", "", "All (*)")
        if fileName:
            self.VFileTextEditH.setText(fileName)

    def videoExtract(self):
        # pindah ke page extract
        self.stackedWidget.setCurrentIndex(7)

    def videoExtractFile(self):
        # tombol extract file
        self.video_path_input = self.VPathTextEditE.toPlainText()
        key = self.VKeyTextEditE.toPlainText()
        self.stegoVideo = StegoVideo(key, self.video_path_input)
        self.stegoVideo.extract_data()
        self.VSaveMessage.show()
        self.VPlayVideoE.show()
        self.VSaveMessage.clicked.connect(self.saveMessageFromVideo)
        self.VPlayVideoE.clicked.connect(self.playVideo)

    def saveMessageFromVideo(self):
        fileName, _ = QFileDialog.getSaveFileName(None, "Save Message Stego Video", self.stegoVideo.filename, "All (*)")
        self.stegoVideo.save_extracted_file(fileName)

    def videoHide(self):
        # pindah ke page hide
        self.stackedWidget.setCurrentIndex(8)

    def videoHideFile(self):
        # tombol hide file
        self.video_path_input = self.VPathTextEditH.toPlainText()
        file_path = self.VFileTextEditH.toPlainText()
        key = self.VKeyTextEditH.toPlainText()
        fileName_video, _ = QFileDialog.getSaveFileName(None, "Save Stego Video", "", "Video (*avi)")
        self.fileName_video = fileName_video
        self.stegoVideo = StegoVideo('hide', key, self.video_path_input, fileName_video, file_path, self.VFrameSeqCheck.isChecked(), self.VPixelSeqCheck.isChecked(), self.VEnkripsiCheck.isChecked())
        self.stegoVideo.run()
        self.VPlayVideoH.show()
        self.VPlayVideoH.clicked.connect(self.playVideo)
        # hide.save_stego_audio("example/lol.wav")
        # extractor = StegoAudio(key, "example/lol.wav")
        # extractor.extract_data()
        # extractor.save_extracted_file("example/lala.pdf")
        # psnr("example/test.wav", "example/lol.wav")
        # print(file_path)

    def playVideo(self):
        self.stegoVideo.ffmpeg_playvideo(self.fileName_video)

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
