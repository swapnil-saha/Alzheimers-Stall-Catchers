import copy
import math
import os
import matplotlib.pyplot as plt
import numpy as np
import h5py
import csv
from tqdm import tqdm
import open3d as o3d

from preprocess_images import VideoProcessor, ImageProcessor3D
from point_cloud import PointCloud


class Tester:

    def __init__(self):
        self.data = []

    def test1(self):
        filename = "../../dataset/micro/187558.mp4"
        extractor = VideoProcessor(filename)
        image_collection = extractor.process_video(roi_extraction=True, filter_enabled=True, average_frames=True)

        thresh = int(np.percentile(image_collection.ravel(), 95))
        cloud, labels = ImageProcessor3D().point_cloud_from_collecton(image_collection, threshold=thresh,
                                                                      filter_outliers=True)

        def downsample(pcd):
            print("Downsampled")
            downpcd = pcd.voxel_down_sample(voxel_size=2)
            o3d.visualization.draw_geometries([downpcd])
            return downpcd

        def normals(pcd):
            print("View normals")
            pcd.estimate_normals(search_param=o3d.geometry.KDTreeSearchParamHybrid(radius=0.1, max_nn=30))
            o3d.visualization.draw_geometries([pcd], point_show_normal=True)
            return pcd

        def hull(pcd):
            print("Define parameters used for hidden_point_removal")
            diameter = np.linalg.norm(np.asarray(pcd.get_max_bound()) - np.asarray(pcd.get_min_bound()))
            radius = diameter * 100

            camera = [0, 0, diameter]
            _, pt_map = pcd.hidden_point_removal(camera, radius)
            pcd_hull = pcd.select_by_index(pt_map)
            o3d.visualization.draw_geometries([pcd_hull])

            return pcd_hull

        def bpa_mesh(pcd):
            pcd.estimate_normals(search_param=o3d.geometry.KDTreeSearchParamHybrid(radius=1, max_nn=30))

            distances = pcd.compute_nearest_neighbor_distance()
            avg_dist = np.mean(distances)
            radius = 3 * avg_dist
            bpa_mesh = o3d.geometry.TriangleMesh.create_from_point_cloud_ball_pivoting(pcd,o3d.utility.DoubleVector([radius, radius * 2]))

            dec_mesh = bpa_mesh.simplify_quadric_decimation(100000)
            dec_mesh.remove_degenerate_triangles()
            dec_mesh.remove_duplicated_triangles()
            dec_mesh.remove_duplicated_vertices()
            dec_mesh.remove_non_manifold_edges()

            o3d.visualization.draw_geometries([bpa_mesh])

    def test2(self):
        filename = "../../dataset/micro/100109.mp4"
        extractor = VideoProcessor(filename)
        image_collection = extractor.process_video(roi_extraction=True, filter_enabled=True, average_frames=True)

        thresh = int(np.percentile(image_collection.ravel(), 95))
        cloud, labels =ImageProcessor3D().point_cloud_from_collecton(image_collection, threshold=thresh,
                                                                      filter_outliers=True)

        for i in range(9):
            if i == 0:
                projection = PointCloud().cloud_projection(cloud=cloud)
            else:
                cloud_rotated = PointCloud().rotate(cloud=cloud, pos=i)
                projection = PointCloud().cloud_projection(cloud=cloud_rotated)
            plt.subplot(3, 3, i+1)
            plt.imshow(projection, cmap='gray')

        plt.show()


if __name__ == "__main__":
    Tester().test2()