# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'confirm.ui'
#
# Created by: PyQt5 UI code generator 5.15.2
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_confirm(object):
    def setupUi(self, confirm):
        confirm.setObjectName("confirm")
        confirm.resize(287, 114)
        self.label = QtWidgets.QLabel(confirm)
        self.label.setGeometry(QtCore.QRect(40, 30, 221, 18))
        font = QtGui.QFont()
        font.setFamily("等线")
        font.setPointSize(10)
        font.setBold(False)
        font.setWeight(50)
        self.label.setFont(font)
        self.label.setTextFormat(QtCore.Qt.PlainText)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setObjectName("label")
        self.save = QtWidgets.QPushButton(confirm)
        self.save.setGeometry(QtCore.QRect(20, 70, 93, 28))
        self.save.setObjectName("save")
        self.drop = QtWidgets.QPushButton(confirm)
        self.drop.setGeometry(QtCore.QRect(170, 70, 93, 28))
        self.drop.setObjectName("drop")

        self.retranslateUi(confirm)
        QtCore.QMetaObject.connectSlotsByName(confirm)

    def retranslateUi(self, confirm):
        _translate = QtCore.QCoreApplication.translate
        confirm.setWindowTitle(_translate("confirm", "确认"))
        self.label.setText(_translate("confirm", "改动未保存，是否放弃修改？"))
        self.save.setText(_translate("confirm", "保存并退出"))
        self.drop.setText(_translate("confirm", "放弃保存"))