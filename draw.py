import cv2
import numpy as np
from PyQt4 import QtCore, QtGui
import sys
import sip
from display import Display
sip.setapi('QString', 1)
sip.setapi('QVariant', 1)
class Draw():
	def __init__(self):
		pass	
	def drawPattern(self,window,palm,previous):
		self.window = window
		print palm, ' palm previous' ,previous
		painter = QtGui.QPainter()
		painter.begin(self.window.image)
		painter.setPen(window.color)		
		palmco = palm[0]
		prevco = previous[0]
		x1 , y1 = palmco
		if previous == [0 , 0]:		
			x2 = 0
			y2 = 0
		else:
			x2, y2 = prevco
			if( ( x2 > x1 + 50 or y2 > y1 + 50 ) or ( x1 > x2 + 50 or y1 > y2 + 50 )):			
				painter.drawLine(x1,y1,x2,y2)
				painter.end()
				self.window.label_Image.setPixmap(QtGui.QPixmap.fromImage(window.image))
				window.show()	
	#	self.paintEvent(palm,previous)
	#def paintEvent(self,palm,previous):
	#	super(self.window.image(), self).paintEvent(palm,previous)
	#	qp = QPainter()
	#	qp.begin(self.window.image())
		#square = QRect(10, 10, 30, 30)
		#qp.drawEllipse(square)
		
	#	qp.end()
