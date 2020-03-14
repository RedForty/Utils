# =+------------------------------------------------------------------------+= #
# Imports

from Qt import QtWidgets, QtGui, QtCompat # pylint:disable=E0611
import maya.OpenMaya as om
import maya.OpenMayaUI as omui
from maya import cmds, mel


# =+------------------------------------------------------------------------+= #
# Public Class

class Timeline_Overlay(QtWidgets.QWidget):
    def __init__(self, frame_times=[0.0], active_color=(150, 150, 150, 100)):

        self.time_control_widget = self._get_time_widget()

        if self.time_control_widget:
            super(Timeline_Overlay, self).__init__(self.time_control_widget)
        else:
            self.close()
            self.deleteLater()

        self.frame_times = []
        self.active_color = []
        self.alpha = 100.0 # Difficult to screw up color input
        self.set_frames(frame_times) # Clean the frame range
        self.set_color(active_color) # Clean up the color input

        self.show()


    # ------------------------------------------------------------------------ #
    # Private methods

    def _get_time_widget(self):
        widget = omui.MQtUtil.findControl(self._get_time_control())
        return QtCompat.wrapInstance(long(widget), QtWidgets.QWidget)

    def _get_time_control(self):
        return mel.eval('$tmpVar = $gPlayBackSlider')

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


    # ------------------------------------------------------------------------ #
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


    # ------------------------------------------------------------------------ #
    def paintEvent(self, paint_event):
        parent = self.parentWidget()
        if parent:
            # ---------------------------------------------------------------- #
            # Basic frame geometry stuff
            self.setGeometry(parent.geometry()) # Make it the same size

            range_start = cmds.playbackOptions(query=True, minTime=True)
            range_end   = cmds.playbackOptions(query=True, maxTime=True)
            displayed_frame_count = range_end - range_start + 1

            height = self.parent().height()
            padding = self.width() * 0.005
            frame_width = (self.width() * 0.99) / displayed_frame_count

            # ---------------------------------------------------------------- #
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

            # ---------------------------------------------------------------- #
            # Can support individual frames with groups, etc..
            for frame_group in list(self._group(self.frame_times)):

                range_frame_times = max(frame_group) - min(frame_group) + 1
                start_frame = frame_group[0]
                start_width = frame_width * (start_frame-range_start) + 1
                end_width = frame_width * range_frame_times

                painter.fillRect(padding + start_width,
                                 0,
                                 end_width-2,
                                 height,
                                 fill_color)
                painter.drawRect(padding + start_width,
                                 1, # Watch out for stroke thickness
                                 end_width-2,
                                 height-2)


# =+------------------------------------------------------------------------+= #
# Developer section

if __name__ == '__main__':
    try:
        test_ui.close() # pylint:disable=E0601
        test_ui.deleteLater()
    except:
        pass

    test_ui = Timeline_Overlay()
    test_ui.set_frames([[-10,20],25,39,40,[50,100]])
    test_ui.set_color([60,100,160])
    test_ui.set_alpha(100)


'''
w = QtCompat.wrapInstance(long(omui.MQtUtil.findControl('graphEditor1GraphEdImpl')), QtWidgets.QWidget)
w.children()[0].close()
w.children()[0].deleteLater()
'''
