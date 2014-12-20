#!/usr/bin/python 
# -*- coding: utf-8 -*-
from PyQt4 import QtCore, QtGui, uic
from lidar.Vec2d import Vec2d
import logging

logger = logging.getLogger(__name__)

class DataView(QtGui.QFrame):
    X_STEP = 10.0
    Y_STEP = 10.0
    SHOW_GRID = False

    def __init__(self, *args):
        QtGui.QFrame.__init__(self, *args)
        self.data = None
        self.press_pos = None
        self.matrix = QtGui.QTransform()
        self.matrix.translate(100, 100)
        
        data = {"primetives":[{"line":{"pos": [10,10], "end": [50, 30]}, "width": 5,"color":(255, 0, 0)},
                              {"text": u"Привет как дела", "pos":[50, 10], "color": (0,255,0)}]}
        
        
        self.draw_data(data)
    
    def sizeHint(self):
        return QtCore.QSize(200, 200)
        

    def mouseMoveEvent(self, event):
        if self.press_pos is not None:
            dp = event.pos() - self.press_pos
            self.press_pos = event.pos()
            self.matrix.translate(dp.x() / self.matrix.m11(), dp.y() / self.matrix.m22())
            self.update()

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.press_pos = event.pos()

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.press_pos = None

    def wheelEvent(self, event):
        s = 1.2 if event.delta() > 0 else 0.8
        self.matrix.scale(s, s)
        self.update()

    def draw_data(self, data):
        '''Отображает данные.
            data - пакет данных для отображения : {
                "primetives": [
                    {"points": [Vec2d,...],
                    "color":(r,g,b,a), - опционально
                    "size": int - опционально},

                    {"line":{"pos": Vec2d, "end": Vec2d}
                     "color": (r,g,b,a) - опционально,
                     "width":int - опционально, толщина линии},

                    {"text":",
                    "pos":[x,y]
                    "color": (r,g,b,a) - опционально}
                    ]
            }
        '''
        self.data = data
        self.update()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.fillRect(event.rect(), QtGui.QBrush(QtCore.Qt.black))
        painter.save()
        self.draw_grid(painter)
        self.draw(painter)
        painter.restore()
    
    def draw_grid(self, painter):
        painter.setPen(QtGui.QPen(QtGui.QBrush(QtGui.QColor(255, 255, 255)), 0.5))
        X_STEP = 10.0
        Y_STEP = 10.0

        p1 = QtCore.QPointF(-10000, 0)
        p2 = QtCore.QPointF(10000, 0)
        
        start_grid = [-1000.0, -1000.0]
        stop_grid = [1000.0, 1000.0]

        if self.SHOW_GRID:
            #линии по x
            for i in range(int((stop_grid[0] - start_grid[0]) / self.X_STEP)):
                p1 = QtCore.QPointF(start_grid[0] + i * self.X_STEP, -start_grid[1])
                p2 = QtCore.QPointF(start_grid[0] + i * self.X_STEP, -stop_grid[1])
                painter.drawLine(self.matrix.map(p1), self.matrix.map(p2))

            #линии по y
            for i in range(int((stop_grid[1] - start_grid[1]) / self.Y_STEP)):
                p1 = QtCore.QPointF(start_grid[0], -(start_grid[1] + i * self.Y_STEP))
                p2 = QtCore.QPointF(stop_grid[0], -(start_grid[1] + i * self.Y_STEP))
                painter.drawLine(self.matrix.map(p1), self.matrix.map(p2))

        painter.setPen(QtGui.QPen(QtGui.QBrush(QtGui.QColor(255, 255, 255)), 1))
        p1 = QtCore.QPointF(start_grid[0], 0)
        p2 = QtCore.QPointF(stop_grid[0], 0)
        painter.drawLine(self.matrix.map(p1), self.matrix.map(p2))

        p1 = QtCore.QPointF(0, -start_grid[1])
        p2 = QtCore.QPointF(0, -stop_grid[0])
        painter.drawLine(self.matrix.map(p1), self.matrix.map(p2))


        # p1 = QtCore.QPointF(0, -10000)
        # p2 = QtCore.QPointF(0, 10000)
        # painter.drawLine(self.matrix.map(p1), self.matrix.map(p2))
    
    def draw(self, painter):
        if self.data is not None and "primetives" in self.data and self.data["primetives"] is not None:
            #llll = [p for p in self.data["primetives"] if "line" in p]
            #print "lines: ", len(llll)
            
            #for p in llll:
            #    self.draw_line(painter, p)
            #return 

            for p in self.data["primetives"]:
                if "points" in p:
                    self.draw_points(painter, p)
                elif "line" in p:
                    self.draw_line(painter, p)
                elif "text" in p:
                    self.draw_text(painter, p)
    
    def draw_points(self, painter, info):
        '''
        Отображает точки, в формате:{
            "points": [Vec2d,...],
            "color":(r,g,b,a), - опционально
            "size": int - опционально
        }
        '''

        #цвет точек
        if "color" in info:
            color = info["color"]
            color = QtGui.QColor(color[0], color[1], color[2])
        else:
            color = QtGui.QColor(255, 255, 255)

        painter.setPen(QtGui.QPen(color))
        painter.setBrush(QtGui.QBrush(color))
        
        #размер точек
        if "size" not in info:
            size = QtCore.QSizeF(2.0, 2.0)
            half_size = QtCore.QPointF(1, 1)
        else:
            size = QtCore.QSizeF(info["size"], info["size"])
            sp = info["size"] / 2.0
            half_size = QtCore.QPointF(sp, sp)
        
        for p in info["points"]:
            p = self.matrix.map(QtCore.QPointF(p[0], -p[1]) - half_size)
            painter.drawEllipse(QtCore.QRectF(p, size))

    def draw_line(self, painter, info):
        '''
        Отображает точки, в формате:{
            "line":{"pos": Vec2d, "end": Vec2d}
            "color": (r,g,b,a) - опционально,
            "width":int - опционально, толщина линии
        }
        '''
        #print "draw_line: ", info

        #цвет точек
        if "color" in info:
            color = info["color"]
            color = QtGui.QColor(color[0], color[1], color[2])
        else:
            color = QtGui.QColor(255, 255, 255)
        
        if "width" in info:
            width = float(info["width"])
        else:
            width = 1.0
        
        painter.setPen(QtGui.QPen(QtGui.QBrush(color), width))
        p1 = QtCore.QPointF(info["line"]["pos"][0], -info["line"]["pos"][1])
        p2 = QtCore.QPointF(info["line"]["end"][0], -info["line"]["end"][1])
        painter.drawLine(self.matrix.map(p1), self.matrix.map(p2))

    def draw_text(self, painter, info):
        '''
        Отображает текст в формате:{
            "text":"",
            "pos":[x,y]
            "color": (r,g,b,a) - опционально
        }
        '''
        if "color" in info:
            color = info["color"]
            color = QtGui.QColor(color[0], color[1], color[2])
        else:
            color = QtGui.QColor(255, 255, 255)

        painter.setPen(color)
        pos = QtCore.QPointF(info["pos"][0], -info["pos"][1])
        painter.drawText(self.matrix.map(pos), info["text"]);
                        
if __name__ == '__main__':
    import sys
    logging.basicConfig(filename='', level=logging.DEBUG)
    logging.getLogger("PyQt4").setLevel(logging.INFO)
    
    app = QtGui.QApplication(sys.argv)
    widget = DataView()
    widget.show()
    sys.exit(app.exec_())
