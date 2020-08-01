
import numpy as np
import copy
import time

import carla
from .carla_sensor import CarlaSensorDataConversion, get_specific_sensor
from .camera.parameters import CameraParams, IntrinsicParams, ExtrinsicParams
from .camera.coordinate_transformation import CoordinateTransformation, rotationMatrix3D
from .camera import basic_tools


# def printVariable(variable):


def world3DToVehicle3D(point_vec, pose):
    '''
    Args:
        point: in world coordinate
        pose: vehicle carla.Transform in world coordinate
    '''
    rotation = pose.rotation
    R = rotationMatrix3D(np.deg2rad(rotation.roll), np.deg2rad(rotation.pitch), np.deg2rad(rotation.yaw))
    t = np.array([pose.location.x, pose.location.y, pose.location.z]).reshape(3,1)
    vehicle_vec = basic_tools.np_dot(R.T, point_vec - t)
    return vehicle_vec


# def getTraj(pose1, pose2, T):
#     x1, x2 = pose1.location.x, pose2.location.x
#     y1, y2 = pose1.location.y, pose2.location.y
#     z1, z2 = pose1.location.z, pose2.location.z
#     theta1, theta2 = np.deg2rad(pose1.rotation.yaw), np.deg2rad(pose2.rotation.yaw)

#     A = np.zeros((6,6))
#     A[0,0] = 1; A[0,1] = T; A[0,2] = T**2
#     A[1,3] = 1; A[1,4] = T; A[1,5] = T**2
#     A[2,0] = 1; A[3,3] = 1
#     A[4,1] = 1; A[4,4] = -theta1
#     A[5,1] = 1; A[5,2] = 2*T; A[5,4] = theta2; A[5,5] = 2*theta2*T

#     b = np.zeros((6,1))
#     b[0,0] = x2; b[1,0] = y2
#     b[2,0] = x1; b[3,0] = y1

#     p = np.dot(np.linalg.inv(A), b)

#     return np.vstack((p.T.reshape(2,3), np.array([z1, z2-z1, 0])))

# def getTimeVec(t):
#     return np.array([1, t, t**2]).reshape(3,1)
# def getDTimeVec(t):
#     return np.array([0, 1, t]).reshape(3,1)

# def getPose(t, p, pose1, pose2):
#     position = np.dot(p, getTimeVec(t))
#     # theta = np.arctan2(np.dot(p[0,:], getDTimeVec(t))[0], np.dot(p[1,:], getDTimeVec(t))[0])
#     # yaw = np.rad2deg(theta)
#     return carla.Transform(carla.Location(x=position[0,0], y=position[1,0], z=position[2,0]), carla.Rotation(yaw=yaw))


def getLinearPose(t, T, pose1, pose2):
    x1, x2 = pose1.location.x, pose2.location.x
    y1, y2 = pose1.location.y, pose2.location.y
    z1, z2 = pose1.location.z, pose2.location.z
    roll1, roll2 = np.deg2rad(pose1.rotation.roll), np.deg2rad(pose2.rotation.roll)
    pitch1, pitch2, = np.deg2rad(pose1.rotation.pitch), np.deg2rad(pose2.rotation.pitch)
    yaw1, yaw2, = np.deg2rad(pose1.rotation.yaw), np.deg2rad(pose2.rotation.yaw)
    tt = t / T

    x, y, z = tt*x2 + (1-tt)*x1, tt*y2 + (1-tt)*y1, tt*z2 + (1-tt)*z1
    roll = np.rad2deg( basic_tools.pi2pi(roll2-roll1) * tt + roll1 )
    pitch = np.rad2deg( basic_tools.pi2pi(pitch2-pitch1) * tt + pitch1 )
    yaw = np.rad2deg( basic_tools.pi2pi(yaw2-yaw1) * tt + yaw1 )
    location = carla.Location(x=x, y=y, z=z)
    rotation = carla.Rotation(roll=roll, pitch=pitch, yaw=yaw)
    return carla.Transform(location, rotation)


class CollectPerspectiveImage(object):
    def __init__(self, param, sensor):
        vehicle_width = param.vehicle_width
        self.longitudinal_sample_number_near = param.longitudinal_sample_number_near
        self.longitudinal_sample_number_far = param.longitudinal_sample_number_far
        

        self.vehicle_half_width = vehicle_width / 2

        # for drawLineInImage
        self.lateral_step_factor = param.lateral_step_factor
        # for drawLineInWorld
        lateral_sample_number = param.lateral_sample_number
        self.lateral_sample_array = np.linspace(-self.vehicle_half_width, self.vehicle_half_width, lateral_sample_number)
        
        self.sensor = sensor
        intrinsic_params = IntrinsicParams(sensor)
        extrinsic_params = ExtrinsicParams(sensor)
        self.camera_params = CameraParams(intrinsic_params, extrinsic_params)

        self.img_width = eval(sensor.attributes['image_size_x'])
        self.img_height = eval(sensor.attributes['image_size_y'])
        self.max_pixel = np.array([self.img_height, self.img_width]).reshape(2,1)
        self.min_pixel = np.array([0, 0]).reshape(2,1)

        self.empty_image = np.zeros((self.img_height, self.img_width, 3), dtype=np.dtype("uint8"))



    def getPM(self, traj_pose_list, vehicle_transform, image):

        empty_image = copy.deepcopy(self.empty_image)

        tick1 = time.time()

        for (time_step, traj_pose) in traj_pose_list:
            self.drawLineInImage(traj_pose, vehicle_transform, empty_image)

        tick2 = time.time()
        tick_pose, tick_draw = 0.0, 0.0

        pose_number = len(traj_pose_list)
        longitudinal_array = np.logspace(self.longitudinal_sample_number_near, self.longitudinal_sample_number_far, pose_number-1, base=2)
        # print(longitudinal_array)
        for i in range(pose_number-1):
            t1, pose1 = traj_pose_list[i][0],   traj_pose_list[i][1]
            t2, pose2 = traj_pose_list[i+1][0], traj_pose_list[i+1][1]
            T = t2-t1
            # traj = getTraj(pose1, pose2, T)
            time_array = np.linspace(0, T, round(longitudinal_array[i]))
            # print(pose1.location, pose1.rotation)
            for t in time_array:
                tick_1 = time.time()
                pose = getLinearPose(t, T, pose1, pose2)
                tick_2 = time.time()
                self.drawLineInImage(pose, vehicle_transform, empty_image)
                tick_3 = time.time()
                tick_pose += tick_2 - tick_1
                tick_draw += tick_3 - tick_2


        tick3 = time.time()
        print('time real: ' + str(tick2-tick1))
        print('time interpolate: ' + str(tick3-tick2))
        print('    time pose: ' +str(tick_pose))
        print('    time draw: ' +str(tick_draw))


        return empty_image





    def drawLineInImage(self, traj_pose, vehicle_transform, empty_image):
        traj_position = traj_pose.location
        traj_vec = np.array([traj_pose.location.x, traj_pose.location.y, traj_pose.location.z]).reshape(3,1)

        # along lateral
        theta = np.deg2rad(traj_pose.rotation.yaw + 90)
        start_vec = np.array([self.vehicle_half_width*np.cos(theta), self.vehicle_half_width*np.sin(theta), 0]).reshape(3,1) + traj_vec
        start_vehicle_vec = world3DToVehicle3D(start_vec, vehicle_transform)
        start_pixel_vec = CoordinateTransformation.world3DToImage2D(start_vehicle_vec, self.camera_params.K, self.camera_params.R, self.camera_params.t)
        start_pixel_vec = start_pixel_vec[::-1,:]

        theta = np.deg2rad(traj_pose.rotation.yaw - 90)
        end_vec = np.array([self.vehicle_half_width*np.cos(theta), self.vehicle_half_width*np.sin(theta), 0]).reshape(3,1) + traj_vec
        end_vehicle_vec = world3DToVehicle3D(end_vec, vehicle_transform)
        end_pixel_vec = CoordinateTransformation.world3DToImage2D(end_vehicle_vec, self.camera_params.K, self.camera_params.R, self.camera_params.t)
        end_pixel_vec = end_pixel_vec[::-1,:]

        flag1 = (start_pixel_vec >= self.min_pixel).all() and (start_pixel_vec < self.max_pixel).all()
        flag2 = (end_pixel_vec >= self.min_pixel).all() and (end_pixel_vec < self.max_pixel).all()
        if not flag1 and not flag2:
            # print('no use')
            return

        length = np.linalg.norm(end_pixel_vec - start_pixel_vec)
        direction = (end_pixel_vec - start_pixel_vec) / length
        lateral_sample_number = round(length / self.lateral_step_factor) + 1
        distance_array = np.linspace(0, length, lateral_sample_number)

        for distance in distance_array:
            pixel_vec = start_pixel_vec + distance * direction
            x_pixel, y_pixel = round(pixel_vec[0,0]), round(pixel_vec[1,0])
            if x_pixel >= 0 and y_pixel >= 0 and x_pixel < self.img_height and y_pixel < self.img_width:
                empty_image[x_pixel,y_pixel,:] = 255

        return


    def drawLineInWorld(self, traj_pose, vehicle_transform, empty_image):
        vec = np.array([traj_pose.location.x, traj_pose.location.y, traj_pose.location.z]).reshape(3,1)
        theta = np.deg2rad(traj_pose.rotation.yaw - 90)

        for distance in self.lateral_sample_array:
            world_vec = np.array([distance*np.cos(theta), distance*np.sin(theta), 0]).reshape(3,1) + vec
            vehicle_vec = world3DToVehicle3D(world_vec, vehicle_transform)
            image_pixel_vec = CoordinateTransformation.world3DToImagePixel2D(vehicle_vec, self.camera_params.K, self.camera_params.R, self.camera_params.t)
            image_pixel_vec = image_pixel_vec[::-1,:]
            if (image_pixel_vec >= self.min_pixel).all() and (image_pixel_vec < self.max_pixel).all():
                x_pixel, y_pixel = image_pixel_vec[0,0], image_pixel_vec[1,0]
                empty_image[x_pixel,y_pixel,:] = 255











