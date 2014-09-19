 # -*- coding: utf8 -*-
import numpy as np
import subprocess
import logging
import time
import os

logger = logging.getLogger(__name__)

class FFmpegReader:
    def __init__(self, save_dir=None, ffmpeg_path="ffmpeg"):
        self.ffmpeg_path = ffmpeg_path
        
        self.size = (320, 240)
        self.buffer_size = self.size[0] * self.size[1] * 3
        self.nc_proc = None
        self.proc = None
        self.save_dir = save_dir
        self.fps = 25
        self.dt = 1.0 / self.fps
        self.cur_time = None
        

        if self.save_dir is not None:
            if not os.path.exists(self.save_dir):
                os.makedirs(self.save_dir)
               
   
    def process_file(self, url, size=None, start_pos=0):
        if size is not None:
            self.size = size
            self.buffer_size = self.size[0] * self.size[1] * 3

        
        params = u"{path} -ss {start_pos} -i {url} -f rawvideo -pix_fmt bgr24 -s {width}x{height} -".format(
                    start_pos=start_pos, path=os.path.join(self.ffmpeg_path, "ffmpeg"), url=url,
                    width=self.size[0], height=self.size[1])
        logger.info(params)
        self.proc = subprocess.Popen(params, stdout=subprocess.PIPE)

    def process_direct_show_video(self, video_device_name="USB2.0 PC CAMERA", size=None):
        if size is not None:
            self.size = size
            self.buffer_size = self.size[0] * self.size[1] * 3

        
        params = u"{path} -f dshow -i video=\"{video_device_name}\" -f rawvideo -pix_fmt rgb24 -s {width}x{height} -".format(
                    path=os.path.join(self.ffmpeg_path, "ffmpeg"),
                    url=url,
                    width=self.size[0],
                    height=self.size[1],
                    video_device_name=video_device_name)
        logger.info(u"process_direct_show_video params:{}".format(params))
        self.proc = subprocess.Popen(params, stdout=subprocess.PIPE)

        
    def process_net_stream(self, port, size=None):
        if size is not None:
            self.size = size
            self.buffer_size = self.size[0] * self.size[1] * 3
        nc_params = u"{path} -l -p {port}".format(path=os.path.join(self.ffmpeg_path, "nc"), port=port)
        logger.info(nc_params)
        self.nc_proc = subprocess.Popen(nc_params, stdout=subprocess.PIPE)

        if self.save_dir is None:
            params = u"{path} -y -f h264 -i - -f rawvideo -pix_fmt bgr24 -s {width}x{height} -".format(port = port,
                     path=os.path.join(self.ffmpeg_path, "ffmpeg"), width = self.size[0], height = self.size[1])
        else:
            params = u"{path} -y -f h264 -i - -c:v copy {out_file} -f rawvideo -pix_fmt bgr24 -s {width}x{height} -".format(port = port,
                     path=os.path.join(self.ffmpeg_path, "ffmpeg"),
                     width = self.size[0],
                     height = self.size[1],
                     out_file = os.path.join(self.save_dir, "{}.mp4".format(time.strftime("%d__%b__%Y__%H_%M_%S", time.gmtime()))))
        logger.info(params)
        self.proc = subprocess.Popen(params, stdin=self.nc_proc.stdout, stdout=subprocess.PIPE)

    def process_ip_camera(self, url, size=None):
        if size is not None:
            self.size = size
            self.buffer_size = self.size[0] * self.size[1] * 3

        if self.save_dir is None:
            params = u"{path} -y -f mjpeg -i {url} -f rawvideo -pix_fmt bgr24 -s {width}x{height} -".format(
                     path=os.path.join(self.ffmpeg_path, "ffmpeg"), width = self.size[0], height = self.size[1], url = url)
        else:
            params = u"{path} -y -f mjpeg {url} -c:v copy {out_file} -f rawvideo -pix_fmt bgr24 -s {width}x{height} -".format(
                     path=os.path.join(self.ffmpeg_path, "ffmpeg"),
                     width = self.size[0],
                     height = self.size[1],
                     out_file = os.path.join(self.save_dir, "{}.mp4".format(time.strftime("%d__%b__%Y__%H_%M_%S", time.gmtime()))),
                     url = url)
        logger.info(params)
        self.proc = subprocess.Popen(params, stdout=subprocess.PIPE)

        
    def read(self):
        data = self.read_string()

        if len(data) < self.buffer_size:
            return (False, None)
        
        res = np.fromstring(data, dtype=np.uint8)
        res.shape = (self.size[1], self.size[0], 3)

        if self.cur_time is None:
            self.cur_time = time.time()
        else:
            cur_time = time.time()
            dt = cur_time - self.cur_time

            if dt <= self.dt:
                time.sleep(self.dt - dt)
                self.cur_time = time.time()
            else:
                self.cur_time = time.time()
            
        return (True, res)
    
    def read_string(self):
        return self.proc.stdout.read(self.buffer_size)
    
    def release(self):
        try:
            logger.info("->")
            if self.nc_proc is not None:
                self.nc_proc.stdout.close()
                self.proc.wait()
            elif self.proc is not None:
                self.proc.terminate()
        finally:
            logger.info("<-")

if __name__ == "__main__":
    logging.basicConfig(level=10, format="%(levelname)s %(name)s::%(funcName)s %(message)s")
    r = FFmpegReader()
    
    #r.process_file("ffmpeg\\out.h264")
    r.process_net_stream(5001)
    while 1:
        res = r.read()
        print res

        if not res[0]:
            break
    
    
    