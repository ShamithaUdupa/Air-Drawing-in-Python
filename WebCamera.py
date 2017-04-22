import cv2
import numpy as np
import math
from handRecognition import HandRecognition

class WebCamera():
	
	def __init__(self,window):
		self.window = window		
	def startcapture(self):					
		
		self.cam = cv2.VideoCapture(0)
		handRecognition = HandRecognition(self.cam,self.window)
		background_captured = 0
		capture_done = 0
		capture_box_count=9
		capture_box_dim=20
		capture_box_sep_x=8
		capture_box_sep_y=18
		capture_pos_x=500
		capture_pos_y=150
		cap_region_x_begin=0.5 # start point/total width
		cap_region_y_end=0.9 # start point/total width

		while(1):
			ret, frame = self.cam.read()
			frame=cv2.bilateralFilter(frame,5,50,100)
			frame=cv2.flip(frame,1)
			cv2.rectangle(frame,(int(cap_region_x_begin*frame.shape[1]),0),(frame.shape[1],int(cap_region_y_end*frame.shape[0])),(255,0,0),1)
			frame_original=np.copy(frame)
			if (background_captured) :
				fg_frame = handRecognition.background_remove(frame,background_model)
			if ( not (background_captured and capture_done)):
				frame,box_pos_x,box_pos_y = handRecognition.set_background(frame,background_captured,capture_done)
			else:
				frame, image = handRecognition.hand_threshold(frame,frame_original,fg_frame,hand_histogram)		
			cv2.imshow('Camera',frame)
			cv2.imshow('Threshold',ret)			
			interrupt = cv2.waitKey(10)	
			if(interrupt & 0xFF == ord('q')):
				break
			elif(interrupt & 0xFF == ord('b')):
				background_model = cv2.createBackgroundSubtractorMOG2(0,10)
				background_captured = 1		
			elif(interrupt & 0xFF == ord('c')):
				capture_done = 1
				hand_histogram = handRecognition.hand_capture(frame_original,box_pos_x,box_pos_y)
			elif(interrupt & 0xFF == ord('t')):
				capture_done = 0
				background_captured = 0				
		self.stopcapture()

	def stopcapture(self):
		self.cam.release()
		cv2.destroyAllWindows()

#if flag == 0:
#			self.startcapture()
#		else:
#			self.stopcapture()
	
			
			
