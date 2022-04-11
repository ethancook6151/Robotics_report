#!/usr/bin/env python3

import rospy
import tf2_ros
from tf.transformations import *
from geometry_msgs.msg import Quaternion
import tf2_geometry_msgs
from robot_vision_lectures.msg import SphereParams 
from ur5e_control.msg import Plan
from geometry_msgs.msg import Twist

sphere_x = 0
sphere_y = 0
sphere_z = 0
sphere_radius = 0 

# Adds points to plan
def add_point(linearX, linearY, linearZ, angularX, angularY, angularZ, plan):
	point = Twist()
		
	point.linear.x = linearX
	point.linear.y = linearY
	point.linear.z = linearZ
	point.angular.x = angularX
	point.angular.y = angularY
	point.angular.z = angularZ
		
	plan.points.append(point)

# Gets sphere raw data
def get_sphere(data):	
	global sphere_x
	global sphere_y
	global sphere_z
	global sphere_radius
	
	sphere_x = data.xc
	sphere_y = data.yc
	sphere_z = data.zc
	sphere_radius = data.radius

	
if __name__ == '__main__':
	# Initialize the node
	rospy.init_node('planner', anonymous = True)
	# Subscriber for sphere parameters
	rospy.Subscriber('sphere_params', SphereParams, get_sphere)
	# Publisher for sending joint positions
	plan_pub = rospy.Publisher('/plan', Plan, queue_size = 10)
	# Set a 10Hz frequency
	loop_rate = rospy.Rate(10)
	
	while not rospy.is_shutdown():
		# add a ros transform listener
		tfBuffer = tf2_ros.Buffer()
		listener = tf2_ros.TransformListener(tfBuffer)
	
		try:
			trans = tfBuffer.lookup_transform("base", "camera_color_optical_frame", rospy.Time())
		except (tf2_ros.LookupException, tf2_ros.ConnectivityException, tf2_ros.ExtrapolationException):
			print('Frames not available')
			loop_rate.sleep()
			continue
		# Define points in camera frame
		pt_in_cam = tf2_geometry_msgs.PointStamped()
		pt_in_cam.header.frame_id = 'camera_color_optical_frame'
		pt_in_cam.header.stamp = rospy.get_rostime()
		
		pt_in_cam.point.x = sphere_x
		pt_in_cam.point.y = sphere_y
		pt_in_cam.point.z = sphere_z
		
		# Convert points to base frame
		pt_in_base = tfBuffer.transform(pt_in_cam,'base', rospy.Duration(1.0))
		x,y,z,radius = pt_in_base.point.x, pt_in_base.point.y, pt_in_base.point.z, sphere_radius
		
		# Print coor before and after transform 
		print("Before tranformed: \n", "x: ", sphere_x, "y: ", sphere_y, "z: ", sphere_z, "radius: ", sphere_radius, "\n")
		print("Transformed: \n", "x: ", x, "y: ", y, "z: ", z, "radius: ", radius, "\n")
		
		# Define plan
		plan = Plan()
			
		# Starting position 
		add_point(-0.7, -0.23, 0.363, 1.57, 0.0, 0.0, plan)
		# Position with x, y, z + radius
		add_point(x, y, z+radius, 1.57, 0.0, 0.0, plan)
		# Back to Start
		add_point(-0.7, -0.23, 0.363, 1.57, 0.0, 0.0, plan)
	
		# publish the plan
		plan_pub.publish(plan)
		# wait for 0.1 seconds until the next loop and repeat
		loop_rate.sleep()
