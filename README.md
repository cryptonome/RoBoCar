# RoBoCar
This repository is for the robot car development, including main program, sensors test scripts, auto install scripts, helpful tools, etc.
#### Sensors used:
* LiDAR: [Velodyne VLP-16](https://www.velodynelidar.com/vlp-16.html)
* Camera: [MYNT EYE D-1000-120](https://www.myntai.com/mynteye/depth)
* GPS: [千寻 D300-GNSS](https://mall.qxwz.com/market/products/details?name=ouabiwv7762375598)
* IMU： [Xsens MTi-300-2A8G4](https://www.mouser.com/ProductDetail/Xsens/MTI-300-2A8G4?qs=sGAEpiMZZMutXGli8Ay4kNSxHzx9HmD09sFWWfMc%252BdM%3D)

# Install
```bash
cd scripts
bash install.sh
```

# Features
* Camera image reading in python with pybind11
```bash
bash camera/build.sh
python camera/run.py
```
* Camera calibration
```bash
cd scripts
python calibration.py --dir imgs --test left-0001.png
```
* LiDAR data reading
```bash
python LiDAR/lidar.py
```
* IMU data reading
```bash
bash IMU/get_permission.sh
python IMU/mtnode.py
```
* XBox control
  * Right axis up: speed
  * Top axis left and right: rotation
  * Buttom Y: forward
  * Buttom A: backward
  * Buttom LOG: break and stop
  * Hat up and down: increase or reduce max speed
  * Hat right and left: increase or reduce acceleration
```bash
cd controller
bash get_permission.sh
python xbox.py
```

# TODO List
- [ ] Rewrite XBox reading, never use pygame again! Need to test on Windows10, Raspberry Pi, Ubuntu18.04 and deploy on Raspberry Pi.
- [ ] Sensor data synchronize, especially LiDAR data. Need to add timestamps on all sensor data.
- [ ] Visualization interface merge, including 3D LiDAR, camera, GPS, robot velocity, rotation and battery percentage. Independent program with UDP communication may work well.
- [ ] Offline map with GPS calibration, and online navigation system like smart phone app (input GPS and output navigation map).
- [ ] LiDAR and camera external parameter calibration
- [x] IPC code deployment
- [ ] Finish sensor_manager.py and collect new data with RoBoCar.
- [ ] Deep learning code deployment

