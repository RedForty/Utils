from maya import cmds
from Qt import QtGui, QtCore, QtWidgets
import maya.OpenMaya as om
import maya.OpenMayaUI as omu
import shiboken2


class selectedCurveLabel():


    def __init__(self):
        self.labelDimensions = [200,20]
        self.eventIDs = []
        self.ptr = False
        self.frameGeo = []
        self.selectedCurveControlName = 'selectedCurveControlName'
        self.button = False
        self.count = 0


    def getPtr(self):
        try:
            self.ptr = shiboken2.wrapInstance(long(omu.MQtUtil.findControl("graphEditor1GraphEd")), QtWidgets.QWidget)
            return self.ptr
        except:
            return None


    def start(self):
        self.ptr = self.getPtr()
        if self.ptr:
            self.frameGeo = (self.ptr.frameSize().width(), self.ptr.frameSize().height())
            self.selectedCurveControlName = cmds.keyframe(query=True,name=True, sl=True)
            self.button = QtWidgets.QPushButton('selectedCurveControlName', self.ptr)
            self.button.setStyleSheet("background: rgba(60, 80, 125, 50); border: 0px")
            self.button.setGeometry(0, self.frameGeo[1]-self.labelDimensions[1], self.frameGeo[0], self.labelDimensions[1])
            self.startCallbacks()
        else:
            print "Graph Editor not open."
            pass


    def graphEditorWindowDimensions(self, *obj):
        if not self.ptr:
            self.ptr = self.getPtr()
        self.frameGeo = (self.ptr.frameSize().width(), self.ptr.frameSize().height())
        # From left, from top, width, height
        self.button.setGeometry(0, self.frameGeo[1]-self.labelDimensions[1], self.frameGeo[0], self.labelDimensions[1])

    def graphEditorSelectionLabel(self, *obj):
        self.count += 1
        # Failsafe loop to prevent maya from shitting itself
        if self.count > 1:
            self.count = 0
            return

        self.selectedCurveControlName = cmds.keyframe(query=True, name=True, sl=True)

        if self.selectedCurveControlName:
            self.button.show()
            if len(self.selectedCurveControlName) > 1:
                self.button.setText(self.selectedCurveControlName[0] + "...")
            else:
                self.button.setText(self.selectedCurveControlName[0])
        else:
            self.button.setText("")
            self.button.hide()


    def startCallbacks(self):
        self.eventIDs.append(om.MEventMessage.addEventCallback('graphEditorChanged', self.graphEditorWindowDimensions))
        self.eventIDs.append(om.MEventMessage.addEventCallback('graphEditorParamCurveSelected', self.graphEditorSelectionLabel))
        pass


    def kill(self):
        self.button.deleteLater()
        for eventID in self.eventIDs:
            om.MMessage.removeCallback(eventID)
            print "Killing callback: " + str(eventID)
        self.eventIDs = []

def start():
    selCurveLabel = selectedCurveLabel()
    selCurveLabel.start()

def end():
    selCurveLabel.kill()
# selCurveLabel.kill()
# selCurveLabel.eventIDs # The callbackIDs
