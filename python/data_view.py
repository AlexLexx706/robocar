#!/usr/bin/python 
# -*- coding: utf-8 -*-

from PyQt4 import QtCore, QtGui, uic
import pyqtgraph as pg
import logging
logger = logging.getLogger(__name__)

class DataView(pg.GraphicsLayoutWidget):
    def __init__(self, *args):
        pg.GraphicsLayoutWidget.__init__(self, *args)
        #Создадим отображалку
        self.plot = self.addPlot()
        self.plot.showGrid(x=True, y=True)
        self.plot.setAspectLocked()

        #создали точки
        self.spi = pg.ScatterPlotItem()
        self.plot.addItem(self.spi)
        self.first_draw = True

    def draw_data(self, data):
        '''Отображает данные.
            data - пакет данных для отображения : {
                "primetives": [
                    {"points": [Vec2d,...],
                    "color":(r,g,b,a), - опционально
                    "size": int - опционально},
{
                    {"line":{"pos": Vec2d, "end": Vec2d}
                     "color": (r,g,b,a) - опционально,
                     "width":int - опционально, толщина линии},
                    
                    {"text":",
                    "pos":[x,y]
                    "color": (r,g,b,a) - опционально}
                    ]
            }
        '''
        self.spi.clear()
        #рисуем новые данные
        for p in data["primetives"]:
            if "points" in p:
                self.draw_points(p)
            if 0:
                if "line" in p:
                    self.draw_line(p)
                elif "text" in p:
                    self.draw_text(p)

        if self.first_draw:
            self.plot.autoRange()
            self.first_draw = False

    def draw_points(self, info):
        '''
        Отображает точки, в формате:{
            "points": [Vec2d,...],
            "color":(r,g,b,a), - опционально
            "size": int - опционально
        }
        '''
        self.spi.addPoints(pos=info["points"],
                            size=info["size"] if "size" in info else 1,
                            pen=pg.mkPen(info["color"]) if "color" in info else None,
                            brush=pg.mkBrush(info["color"]) if "color" in info else None)

        if 0:
            if "size" in info:
                spi.setSize(info["size"])

            if "color" in info:
                spi.setBrush(pg.mkBrush(info["color"]))
                spi.setPen(pg.mkPen(color=info["color"]))

            self.plot.addItem(spi)

    def draw_line(self, info):
        '''
        Отображает точки, в формате:{
            "line":{"pos": Vec2d, "end": Vec2d}
            "color": (r,g,b,a) - опционально,
            "width":int - опционально, толщина линии
        }
        '''

        line = self.plot.plot([{"x": info["line"]["pos"][0], "y":info["line"]["pos"][1]},
                        {"x": info["line"]["end"][0], "y":info["line"]["end"][1]}])

        if "color" in info :
            if "width" in info:
                line.setPen(color=info["color"], width=info["width"])
            else:
                line.setPen(color=info["color"])

        #Вместе с текстом
        if "text" in info:
            if "color" in info["color"]:
                text = pg.TextItem(info["text"], color=info["color"])
            else:
                text = pg.TextItem(info["text"])

            text.setPos(info["line"]["pos"][0], info["line"]["pos"][1])
            self.plot.addItem(text)

    def draw_text(self, info):
        '''
        Отображает текст в формате:{
            "text":"",
            "pos":[x,y]
            "color": (r,g,b,a) - опционально
        }
        '''

        if "color" in info:
            text = pg.TextItem(info["text"], color=info["color"])
        else:
            text = pg.TextItem(info["text"])

        text.setPos(info["pos"][0], info["pos"][1])
        self.plot.addItem(text)

if __name__ == '__main__':
    import sys
    logging.basicConfig(filename='', level=logging.DEBUG)
    logging.getLogger("PyQt4").setLevel(logging.INFO)
    
    app = QtGui.QApplication(sys.argv)
    widget = DataView()
    widget.show()
    sys.exit(app.exec_())
