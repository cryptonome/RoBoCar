import cv2
import numpy as np

path = "/home/wang/Downloads/collect_data/"
index = '20'

from queue import Queue
import pyqtgraph.opengl as gl
from pyqtgraph.Qt import QtCore, QtGui
import sys


class Visualizer(object):
    def __init__(self, data_queue):
        self.data_queue = data_queue
        self.traces = dict()
        self.app = QtGui.QApplication(sys.argv)
        self.w = gl.GLViewWidget()
        self.w.opts['distance'] = 40
        self.w.setWindowTitle('Visualizer')
        self.w.setGeometry(0, 110, 1920, 1080)
        self.w.show()

        # create the background grids
        gx = gl.GLGridItem()
        gx.rotate(90, 0, 1, 0)
        gx.translate(-10, 0, 10)
        self.w.addItem(gx)
        gy = gl.GLGridItem()
        gy.rotate(90, 1, 0, 0)
        gy.translate(0, -10, 10)
        self.w.addItem(gy)
        gz = gl.GLGridItem()
        gz.translate(0, 0, 0)
        self.w.addItem(gz)

        pts = np.array([[0,0,0]])
        self.traces[0] = gl.GLScatterPlotItem(pos=pts, color=(1.,1.,1.,0.), size=0.1)
        self.w.addItem(self.traces[0])
        
        self.points = pts

    def start(self):
        if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
            QtGui.QApplication.instance().exec_()
            
    def close(self):
        QtGui.QApplication.instance().quit()

    def set_plotdata(self, points, color):
        self.traces[0].setData(pos=points, color=color)

    def update(self):
        if not self.data_queue.empty():
            pts = self.data_queue.get()
            self.points = pts

        self.set_plotdata(
            points=self.points,
            color=(0.,1.,1.,1.)#self.get_color(self.points)
        )

    def animation(self):
        timer = QtCore.QTimer()
        timer.timeout.connect(self.update)
        timer.start(16)
        self.start()
        
    def get_color(self, pts):
        z_max = np.max(pts, axis=0)[2]
        z_min = np.min(pts, axis=0)[2]
        z_avg = np.mean(pts, axis=0)[2]
        delta = min(z_max - z_avg, z_avg - z_min)
        z_max = z_avg + delta
        z_min = z_avg - delta
        
        colors = np.ones((pts.shape[0], 4))
        for i in range(len(pts)):
            color = (pts[i][2] - z_min)/(z_max - z_min)
            color = max(0, min(color, 1))
            colors[i][0] = 2*color-1 if color > 0.5 else 0
            colors[i][1] = 2 - 2*color if color > 0.5 else 2*color
            colors[i][2] = 0 if color > 0.5 else 1 - 2*color
        return colors
    
def read_pcd(file_path):
    x = []
    y = []
    z = []
    intensity = []
    with open(file_path, 'r') as file:
        lines = file.readlines()
        [lines.pop(0) for _ in range(9)]
        for line in lines:
            sp_line = line.split()
            if float(sp_line[0]) < 0:
                continue
            x.append(float(sp_line[0]))
            y.append(float(sp_line[1]))
            z.append(float(sp_line[2]))
            intensity.append(float(sp_line[3]))
    return np.array([x, y, z]), intensity

width = 1280
height = 720

fx = 711.642238
fy = 711.302135
s = 0.0
x0 = 644.942373
y0 = 336.030580

cameraMat = np.array([
        [fx,  s, x0],
        [0., fy, y0],
        [0., 0., 1.]
])

distortionMat = np.array([-0.347125, 0.156284, 0.001037, -0.000109 ,0.000000])

#img = cv2.imread(path+'left_'+index+'.png')
img = cv2.imread('12345.png')

point_cloud, intensity = read_pcd(path+'cloud_'+index+'.pcd')


theta_y = 18*np.pi/180.

pitch_rotationMat = np.array([
    [np.cos(theta_y),  0., np.sin(theta_y)],
    [       0.,        1.,         0.     ],
    [-np.sin(theta_y), 0., np.cos(theta_y)],
])


rotationMat = np.array([
    [-0.0024, -1.0000, -0.0033],
    [0.0746,  0.0031,  -0.9972],
    [0.9972,  -0.0026, 0.0746],
])
translationMat = np.array([0.0660, 0.1263, 0.2481])


theta_x = np.arctan2(rotationMat[2][1], rotationMat[2][2])
#theta_y =  np.arctan2(-rotationMat[2][0], np.sqrt(rotationMat[2][1]**2 + rotationMat[2][2]**2))
#theta_z = np.arctan2(rotationMat[1][0], rotationMat[0][0])
#print(theta_x*180./np.pi, theta_y*180./np.pi, theta_z*180./np.pi)



point_cloud = np.dot(pitch_rotationMat, point_cloud)
rotationMat = np.dot(rotationMat, np.linalg.inv(pitch_rotationMat))
translationMat = np.dot(translationMat, np.linalg.inv(pitch_rotationMat))

intensity = [100]*1000000

def lidar2camera(point_cloud, rotationMat, translationMat):
    trans_pc = np.dot(rotationMat, point_cloud) + np.tile(translationMat, (point_cloud.shape[1], 1)).T

    image_uv = np.array([
            trans_pc[0]*fx/trans_pc[2] + x0,
            trans_pc[1]*fy/trans_pc[2] + y0
            ])
    
    
    point_size = 1
    thickness = 4
    for i in range(image_uv.shape[1]):
        point = (int(image_uv[0][i]), int(image_uv[1][i]))
        if point[0] > width or point[0] < 0 or point[1] > height or point[1] < 0:
            continue
        if intensity[i] < 1: continue
        cv2.circle(img, point, point_size, ((100.-intensity[i])*0.01*255, 0, intensity[i]*0.01*255), thickness)

    cv2.imwrite('merge_'+index+'.png',img) 


####################################

x= []
y = []
for i in range(1280):
    for j in range(720):
        if img[j][i][2] > 220 and img[j][i][0] < 50 and img[j][i][1] < 50:
            x.append(i)
            y.append(j)


image_uv = np.array([
        x,
        y
        ])

z0 = -1.55
def camera2lidar(image_uv):
    rotation = np.linalg.inv(np.dot(cameraMat, rotationMat))
    translation = np.dot(cameraMat, translationMat)
    translation = np.dot(rotation, translation)
    R = rotation
    T = translation
    roadheight = -1.55
    
    u = image_uv[0]
    v = image_uv[1]
    
    zi = (T[2]+roadheight)/(R[2][0]*u + R[2][1]*v + R[2][2])
    xl = (R[0][0]*u + R[0][1]*v + R[0][2])*zi - T[0]
    yl = (R[1][0]*u + R[1][1]*v + R[1][2])*zi - T[1]
    trans_pc = np.array([
            xl,
            yl,
            [z0]*image_uv.shape[1]
            ])
    #return trans_pc
    trans_pc = np.hstack((trans_pc,point_cloud))
    data_queue = Queue(10)
    data_queue.put(trans_pc.T)
    v = Visualizer(data_queue)
    v.animation()


trans_pc = camera2lidar(image_uv)
#lidar2camera(trans_pc, rotationMat, translationMat)