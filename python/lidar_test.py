# -*- coding: utf-8 -*-
from lidar import lidar, LineFeaturesMaker
from Queue import Queue
from threading import Thread
import time

def make_features_proc(data_queue):
    lfm = LineFeaturesMaker.LineFeaturesMaker()
    
    while 1:
        data = data_queue.get()
        if data is None:
            return
        clusters = lfm.sector_to_clusters(data)
        lines = lfm.clusters_to_lines(clusters)
        lfm.get_distances(lines)

def main_fun():
    out_queue = Queue(2)
    l = lidar.Lidar(out_queue)
    l.start()
    try:
        make_features_proc(out_queue)
    except KeyboardInterrupt:
        pass
    l.stop()

if __name__ == "__main__":
    #import cProfile
    #cProfile.run('main_fun()')
    main_fun()
