# =+-----------------------------------------------------------------------+= #
# Imports

from Qt import QtWidgets, QtGui, QtCompat # pylint:disable=E0611
import maya.OpenMaya as om
import maya.OpenMayaUI as omui
from maya import cmds


# =+-----------------------------------------------------------------------+= #
# Public Class

class GE_Overlay(QtWidgets.QWidget):
    def __init__(self, frame_times=[0.0], active_color=(150, 150, 150, 100)):
        self.ge_widget = self._get_graphEditor()
        if self.ge_widget:
            super(GE_Overlay, self).__init__(self.ge_widget)
        else:
            self.close()
            self.deleteLater()

        self.frame_times = []
        self.active_color = []
        self.alpha = 100.0 # Difficult to screw up color input
        self.set_frames(frame_times) # Clean the frame range
        self.set_color(active_color) # Clean up the color input

        self.show()


    # ----------------------------------------------------------------------- #
    # Private methods

    def _get_graphEditor(self):
        try:
            widget = omui.MQtUtil.findControl('graphEditor1GraphEdImpl')
            return QtCompat.wrapInstance(long(widget), QtWidgets.QWidget)
        except TypeError:
            cmds.error('No GraphEditor found!')
            return None

    def _clamp(self, n, smallest, largest):
        return max(smallest, min(n, largest))

    def _group(self, L):
        first = last = L[0]
        for n in L[1:]:
            if n - 1 == last: # Part of the group, bump the end
                last = n
            else: # Not part of the group, yield current group and start a new
                yield first, last
                first = last = n
        yield first, last # Yield the last group


    # ----------------------------------------------------------------------- #
    # Public methods

    def set_frames(self, frames):
        '''
        It's possible to send a list with ranges as 2-item lists.
        For example, [[-10,20],25,39,[50,100]]
        '''
        new_frame_times = []
        if not isinstance(frames, list): frames = [frames]
        for frame in frames:
            if isinstance(frame, list):
                frame = frame if frame[0]<frame[1] else [frame[1],frame[0]]
                frame_range = range(frame[0], frame[1]+1)
                new_frame_times.extend(frame_range )
            else:
                new_frame_times.append(frame)
        self.frame_times = list(set(new_frame_times))
        self.frame_times.sort()
        self.update()

    def get_frames(self):
        return self.frame_times

    def set_color(self, color):
        ''' Set either rgb or rgba (255,255,255,255)'''
        if not isinstance(color, list): color = [color]
        if len(color) == 3:
            self.active_color = color
        elif len(color) == 4:
            self.active_color = color[:3] # Assuming the 4th is alpha
            self.alpha = color[-1]
        self.update()

    def set_alpha(self, alpha):
        ''' Set alpha 0-255 '''
        if not isinstance(alpha, float): alpha = float(alpha)
        self.alpha = alpha
        self.update()


    # ----------------------------------------------------------------------- #
    def paintEvent(self, paint_event):
        parent = self.parentWidget()
        if parent:
            # --------------------------------------------------------------- #
            # Basic frame geometry stuff
            self.setGeometry(parent.geometry())

            frame_width  = self.ge_widget.frameSize().width()
            frame_height = self.ge_widget.frameSize().height()

            # Get initial frame range of GE panel
            # Taken from the maya docs for MGraphEditorInfo()
            leftSu=om.MScriptUtil(0.0)
            leftPtr=leftSu.asDoublePtr()
            rightSu=om.MScriptUtil(0.0)
            rightPtr=rightSu.asDoublePtr()
            bottomSu=om.MScriptUtil(0.0)
            bottomPtr=bottomSu.asDoublePtr()
            topSu=om.MScriptUtil(0.0)
            topPtr=topSu.asDoublePtr()

            omui.MGraphEditorInfo().getViewportBounds(leftPtr,
                                                      rightPtr,
                                                      bottomPtr,
                                                      topPtr)

            ge_left_frame = om.MScriptUtil(leftPtr).asDouble()
            ge_right_frame = om.MScriptUtil(rightPtr).asDouble()

            # Distance in numbers of frames visible in the widget
            total_visible_frames = ge_right_frame - ge_left_frame # It floats!

            # --------------------------------------------------------------- #
            # Painter widgets
            painter = QtGui.QPainter(self)
            fill_color = QtGui.QColor(*self.active_color)
            fill_color.setAlpha(self.alpha)

            pen = painter.pen()
            pen.setWidth(1)
            highlight_color = \
                [self._clamp(x + 10, 0, 255) for x in self.active_color]
            pen_color = QtGui.QColor(*highlight_color)
            pen_color.setAlpha(self._clamp(self.alpha * 2, 0, 255))
            pen.setColor(pen_color)
            painter.setPen(pen)

            for frame_group in list(self._group(self.frame_times)):
                # Start frame calculated against the width of the frame
                ratio_left_side = (frame_group[0] - ge_left_frame)\
                                   / total_visible_frames
                left_side_geometry = ratio_left_side * frame_width

                # End frame calculated against the width of the frame
                ratio_right_side = (frame_group[-1] - ge_left_frame + 1)\
                                    / total_visible_frames
                right_side_geometry = ratio_right_side * frame_width

                painter.fillRect(left_side_geometry,
                                 0, # From the top
                                 right_side_geometry-left_side_geometry,
                                 frame_height, # To the bottom
                                 fill_color)
                painter.drawRect(left_side_geometry,
                                 -1, # Watch out for stroke thickness
                                 right_side_geometry-left_side_geometry,
                                 frame_height+2)


# =+----------------------------------------------------------------------+= #
# Developer section

if __name__ == '__main__':
    try:
        test_ui.close() # pylint:disable=E0601
        test_ui.deleteLater()
    except:
        pass

    test_ui = GE_Overlay()
    test_ui.set_frames([[-10,20],25,39,40,[50,100]])
    test_ui.set_color([60,100,160])
    test_ui.set_alpha(100)


'''
w = QtCompat.wrapInstance(long(omui.MQtUtil.findControl('graphEditor1GraphEdImpl')), QtWidgets.QWidget)
w.children()[0].close()
w.children()[0].deleteLater()
'''
