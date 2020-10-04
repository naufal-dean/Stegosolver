import os
import sqlite3
import time
from PyQt5.uic import loadUi
from PyQt5.Qt import QAbstractItemView
from PyQt5.QtWidgets import QTableWidget, QHeaderView, QTableWidgetItem, QMainWindow, QFileDialog
from PyQt5.QtCore import Qt, QTimer
from datetime import date
from controller import StegoImage, StegoAudio
from controller.audio_controller import psnr

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        loadUi(os.getcwd() + '/ui/main.ui', self)

        self.stackedWidget.setCurrentIndex(0)
        self.audioButton.clicked.connect(self.audio)

    def audio(self):
        self.stackedWidget.setCurrentIndex(1)
        self.AHidePageButton.clicked.connect(self.audioHide)

    def audioHide(self):
        self.stackedWidget.setCurrentIndex(2)
        self.AHideButton.clicked.connect(self.audioHideFile)

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


