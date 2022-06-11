#!/usr/bin/python

"""
Quick Bezier profile editor

...Sorta

"""

from __future__ import division # Need to get floats when dividing intergers
from Qt import QtWidgets, QtGui, QtCore, QtCompat
import maya.OpenMayaUI as mui


def _get_maya_window():
    ptr = mui.MQtUtil.mainWindow()
    return QtCompat.wrapInstance(long(ptr), QtWidgets.QMainWindow) 

class Example(QtWidgets.QDialog):

    def __init__(self):
        super(Example, self).__init__()
        
        self.setParent(_get_maya_window())
        self.setWindowFlags(
            QtCore.Qt.Dialog |
            QtCore.Qt.WindowCloseButtonHint
        )

        self.setProperty("saveWindowPref", True)
        self.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
        
        self.margin = 20
        
        self.x1 = 200
        self.y1 = 0 + self.margin
        
        self.x2 = 200
        self.y2 = 400 - self.margin
        
        self.red  = QtGui.QColor(250, 0, 0  , 150)
        self.blue = QtGui.QColor(  0, 0, 255, 150)
        
        self.initUI()


    def initUI(self):
        self.setGeometry(300, 300, 400, 400)
        self.setWindowTitle('Bezier curve')
        self.show()


    def paintEvent(self, e):
        qp = QtGui.QPainter()
        qp.begin(self)
        qp.setRenderHint(QtGui.QPainter.Antialiasing)
        
        self.drawRectangle(qp, self.margin, self.margin, self.geometry().width()-(2*self.margin), self.geometry().height()-(2*self.margin))
        
        self.drawBezierCurve(qp, self.x1, self.margin, self.x2, 400 - self.margin)
        self.drawLine(qp, self.margin, self.margin, self.x1, self.margin)
        self.drawLine(qp, 400 - self.margin, 400 - self.margin, self.x2, 400 - self.margin)
        self.drawDots(qp, self.x1, self.margin, self.red)
        self.drawDots(qp, self.x2, 400 - self.margin, self.red)
        
        self.drawBezierCurve(qp, self.margin, self.y1, 400 - self.margin, self.y2)
        self.drawLine(qp, self.margin, self.margin, self.margin, self.y1)
        self.drawLine(qp, 400 - self.margin, 400 - self.margin, 400 - self.margin, self.y2)
        self.drawDots(qp, self.margin, self.y1, self.blue)
        self.drawDots(qp, 400 - self.margin, self.y2, self.blue)
        
        qp.end()        


    def drawRectangle(self, qp, x, y, width, height):
        brush = QtGui.QBrush(QtGui.QColor(50, 50, 50))
        pen = QtGui.QPen()
        pen.setColor(QtGui.QColor(192, 192, 192))
        pen.setWidth(1)
        qp.setPen(pen)
        qp.setBrush(brush)
        qp.drawRect(x, y, width, height)
        qp.setBrush(QtCore.Qt.NoBrush)

    
    def drawDots(self, qp, x, y, color):
        pen = QtGui.QPen()
        pen.setColor(color)
        pen.setCapStyle(QtCore.Qt.RoundCap)
        pen.setWidth(10)
        qp.setPen(pen)
        qp.drawPoint(x,y)


    def drawBezierCurve(self, qp, x1, y1, x2, y2):
        pen = QtGui.QPen()
        pen.setColor(QtGui.QColor(192, 192, 192))
        pen.setWidth(1)
        qp.setPen(pen)
        path = QtGui.QPainterPath()
        path.moveTo(self.margin, self.margin)
        path.cubicTo(x1, y1, x2, y2, 400 - (self.margin), 400 - (self.margin))
        qp.drawPath(path)


    def drawLine(self, qp, x0, y0, x1, y1):
        pen = QtGui.QPen()
        pen.setCapStyle(QtCore.Qt.RoundCap)
        pen.setStyle(QtCore.Qt.DotLine)
        pen.setColor(QtGui.QColor(192, 192, 192))
        pen.setWidth(2)
        qp.setPen(pen)
        
        path = QtGui.QPainterPath()
        path.moveTo(x0, y0)
        path.lineTo(x1, y1)
        qp.drawPath(path)
        
        
    def mouseMoveEvent(self, pos):
        
        width = self.geometry().width()
        height = self.geometry().height()
        
        # Start doing math here to symmetrize the vertical
        # and do opposite the horizontal
        
        percentageX = pos.x() / width
        percentageY = pos.y() / height
        
        x1Value = min(max(self.margin, pos.x() * percentageY), 400 - self.margin)
        x2Value = min(max(self.margin, pos.x() * (1.0-percentageY)), 400 - self.margin)
        
        y1Value = min(max(self.margin, pos.y() * percentageX), 400 - self.margin)
        y2Value = min(max(self.margin, pos.y() * (1.0-percentageX)), 400 - self.margin)

        self.x1 = x1Value
        self.x2 = x2Value 
        
        self.y1 = y1Value
        self.y2 = y2Value 
        
        self.update() # Repaint

        
def main():
    global _UI
    try:
        _UI.close()
        _UI.deleteLater()
        _UI = None
    except:
        pass
    finally:
        _UI = Example()


if __name__ == '__main__':
    main()