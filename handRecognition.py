import numpy as np
import cv2
import math
from draw import Draw
hsv_thresh_lower = 150
gaussian_ksize = 11
gaussian_sigma = 0
hsv_thresh_lower=150
gaussian_ksize=11
gaussian_sigma=0
morph_elem_size=13
median_ksize=3
capture_box_count=9
capture_box_dim=20
capture_box_sep_x=8
capture_box_sep_y=18
capture_pos_x=500
capture_pos_y=150
cap_region_x_begin=0.5 # start point/total width
cap_region_y_end=0.8 # start point/total width
finger_thresh_l=2.0
finger_thresh_u=3.8
radius_thresh=0.04 # factor of width of full frame
first_iteration=True
finger_ct_history=[0,0]
previous = [0,0]
class HandRecognition():
	def __init__(self, camera,window):
		self.camera = camera
		self.window = window
		self.draw = Draw()
	
	def background_remove(self,frame,bg_model):
		#global bg_model		
		self.new_frame = frame
		fg_mask=bg_model.apply(self.new_frame)
		kernel = np.ones((3,3),np.uint8)
		fg_mask=cv2.erode(fg_mask,kernel,iterations = 1)
		new_frame=cv2.bitwise_and(self.new_frame,self.new_frame,mask=fg_mask)
		return self.new_frame

	def set_background(self,frame,background_captured,capture_done):
		self.new_frame = frame
		if( not background_captured ):
			cv2.putText(self.new_frame,"Remove hand from the frame and press 'b' to capture background",(int(0.05*self.new_frame.shape[1]),int(0.97*self.new_frame.shape[0])),cv2.FONT_HERSHEY_SIMPLEX,0.5,(0,255,255),1,8)
		else :
			cv2.putText(self.new_frame,"Place hand inside boxes and press 'c' to capture hand histogram",(int(0.08*frame.shape[1]),int(0.97*frame.shape[0])),cv2.FONT_HERSHEY_SIMPLEX,0.5,(0,255,255),1,8)
		first_iteration = True
		box_pos_x=np.array([capture_pos_x,capture_pos_x+capture_box_dim+capture_box_sep_x,capture_pos_x+2*capture_box_dim+2*capture_box_sep_x,capture_pos_x,capture_pos_x+capture_box_dim+capture_box_sep_x,capture_pos_x+2*capture_box_dim+2*capture_box_sep_x,capture_pos_x,capture_pos_x+capture_box_dim+capture_box_sep_x,capture_pos_x+2*capture_box_dim+2*capture_box_sep_x],dtype=int)
		box_pos_y=np.array([capture_pos_y,capture_pos_y,capture_pos_y,capture_pos_y+capture_box_dim+capture_box_sep_y,capture_pos_y+capture_box_dim+capture_box_sep_y,capture_pos_y+capture_box_dim+capture_box_sep_y,capture_pos_y+2*capture_box_dim+2*capture_box_sep_y,capture_pos_y+2*capture_box_dim+2*capture_box_sep_y,capture_pos_y+2*capture_box_dim+2*capture_box_sep_y],dtype=int)
		for i in range(capture_box_count):
			cv2.rectangle(self.new_frame,(box_pos_x[i],box_pos_y[i]),(box_pos_x[i]+capture_box_dim,box_pos_y[i]+capture_box_dim),(255,0,0),1)	
		return self.new_frame,box_pos_x,box_pos_y
	
	def hand_threshold(self,frame,frame_original,fg_frame,hand_hist):
		self.new_frame = frame
		self.new_frame = cv2.medianBlur(self.new_frame,3)
		hsv = cv2.cvtColor(self.new_frame,cv2.COLOR_BGR2HSV)
		hsv[0:int(cap_region_y_end*hsv.shape[0]),0:int(cap_region_x_begin*hsv.shape[1])]=0 # Right half screen only
		hsv[int(cap_region_y_end*hsv.shape[0]):hsv.shape[0],0:hsv.shape[1]]=0
		back_projection = cv2.calcBackProject([hsv], [0,1],hand_hist, [00,180,0,256], 1)
		disc = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (morph_elem_size,morph_elem_size))
		cv2.filter2D(back_projection, -1, disc, back_projection)
		back_projection=cv2.GaussianBlur(back_projection,(gaussian_ksize,gaussian_ksize), gaussian_sigma)
		back_projection=cv2.medianBlur(back_projection,median_ksize)
		ret, thresh = cv2.threshold(back_projection, hsv_thresh_lower, 255, 0)	
		contour_frame = np.copy(thresh)
		image,contours,hierarchy = cv2.findContours(contour_frame,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
		found , hand_contours = self.find_hand_contour(contours)
		if(found):
			hand_convex_hull = cv2.convexHull(hand_contours)
			self.new_frame,hand_center,hand_radius,hand_size_score = self.mark_hand_center(frame_original,hand_contours)
			if(hand_size_score):
				self.new_frame,finger,palm = self.mark_fingers(self.new_frame,hand_convex_hull,hand_center,hand_radius)
			else:
				self.new_frame = frame_original				
		return self.new_frame,image
	
	def mark_hand_center(self,frame_original,hand_contour):
		max_d=0
		pt=(0,0)
		x,y,w,h = cv2.boundingRect(hand_contour)
		for ind_y in xrange(int(y+0.3*h),int(y+0.8*h)): #around 0.25 to 0.6 region of height (Faster calculation with ok results)
			for ind_x in xrange(int(x+0.3*w),int(x+0.6*w)): #around 0.3 to 0.6 region of width (Faster calculation with ok results)
				dist= cv2.pointPolygonTest(hand_contour,(ind_x,ind_y),True)
				if(dist>max_d):
					max_d=dist
					pt=(ind_x,ind_y)
		if(max_d>radius_thresh*frame_original.shape[1]):
			thresh_score=True
			cv2.circle(frame_original,pt,int(max_d),(255,0,0),2)
		else:
			thresh_score=False
		return frame_original,pt,max_d,thresh_score		

	def mark_fingers(self,frame_in,hull,pt,radius): 
		global first_iteration
		global finger_ct_history
		global previous
		finger=[(hull[0][0][0],hull[0][0][1])]
					
		j=0
		cx = pt[0]
		cy = pt[1]
		for i in range(len(hull)):
			dist = np.sqrt((hull[-i][0][0] - hull[-i+1][0][0])**2 + (hull[-i][0][1] - hull[-i+1][0][1])**2)
        	if (dist>18):
				if(j==0):
					finger=[(hull[-i][0][0],hull[-i][0][1])]
				else:
					finger.append((hull[-i][0][0],hull[-i][0][1]))
					j=j+1
     
		temp_len=len(finger)
		i=0
		while(i<temp_len):
			dist = np.sqrt( (finger[i][0]- cx)**2 + (finger[i][1] - cy)**2)
			if(dist<finger_thresh_l*radius or dist>finger_thresh_u*radius or finger[i][1]>cy+radius):
				finger.remove((finger[i][0],finger[i][1]))
				temp_len=temp_len-1
			else:
				i=i+1        
		if(temp_len>5):
			for i in range(1,temp_len+1-5):
				finger.remove((finger[temp_len-i][0],finger[temp_len-i][1]))
		palm=[(cx,cy),radius]
		
		if(first_iteration):
			finger_ct_history[0]=finger_ct_history[1]=len(finger)
			first_iteration=False
		else:
			finger_ct_history[0]=0.34*(finger_ct_history[0]+finger_ct_history[1]+len(finger))
		if((finger_ct_history[0]-int(finger_ct_history[0]))>0.8):
			finger_count=int(finger_ct_history[0])+1
		else:
			finger_count=int(finger_ct_history[0])
		finger_ct_history[1]=len(finger)
		
		
		
		count_text="FINGERS:"+str(finger_count)
		cv2.putText(frame_in,count_text,(int(0.62*frame_in.shape[1]),int(0.88*frame_in.shape[0])),cv2.FONT_HERSHEY_DUPLEX,1,(0,255,255),1,8)

		for k in range(len(finger)):
			cv2.circle(frame_in,finger[k],10,255,2)
			cv2.line(frame_in,finger[k],(cx,cy),255,2)
		print hull, ' ', finger, ' ', palm
		self.draw.drawPattern(self.window,palm,previous)
		previous = palm		
		return frame_in,finger,palm
	
	def find_hand_contour(self,contours):
		max_area=0
		largest_contour=-1
		for i in range(len(contours)):
			cont=contours[i]
			area=cv2.contourArea(cont)
			if(area>max_area):
				max_area=area
				largest_contour=i
		if(largest_contour==-1):
			return False,0
		else:
			h_contour=contours[largest_contour]
		return True,h_contour
	
	def hand_capture(self,frame_in,box_x,box_y):
		hsv = cv2.cvtColor(frame_in, cv2.COLOR_BGR2HSV)
		ROI = np.zeros([capture_box_dim*capture_box_count,capture_box_dim,3], dtype=hsv.dtype)
		for i in xrange(capture_box_count):
			ROI[i*capture_box_dim:i*capture_box_dim+capture_box_dim,0:capture_box_dim] = hsv[box_y[i]:box_y[i]+capture_box_dim,box_x[i]:box_x[i]+capture_box_dim]
		hand_hist = cv2.calcHist([ROI],[0, 1], None, [180, 256], [0, 180, 0, 256])
		cv2.normalize(hand_hist,hand_hist, 0, 255, cv2.NORM_MINMAX)
		print hand_hist
		return hand_hist

		
