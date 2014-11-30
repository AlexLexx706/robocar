from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext

ext_modules = [
    Extension("lidar.lidar",		["lidar/lidar.py"]),
    Extension("lidar.LineFeaturesMaker",		["lidar/LineFeaturesMaker.py"]),
    Extension("lidar.pid",		["lidar/pid.py"]),
    Extension("lidar.Vec2d",		["lidar/Vec2d.py"])
    ]
setup(
    name = 'lidar',
    cmdclass = {'build_ext': build_ext},
    ext_modules = ext_modules
)