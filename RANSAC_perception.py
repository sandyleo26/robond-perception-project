# Import PCL module
import pcl

# Load Point Cloud file
cloud = pcl.load_XYZRGB('test.pcd')

outlier_filter = cloud.make_statistical_outlier_filter()
outlier_filter.set_mean_k(20)
x = 0.3
outlier_filter.set_std_dev_mul_thresh(x)
cloud_filtered = outlier_filter.filter()
pcl.save(cloud_filtered, 'statistically_inliers.pcd')
outlier_filter.set_negative(True)
pcl.save(outlier_filter.filter(), 'statistically_outliers.pcd')

# Voxel Grid filter
vox = cloud_filtered.make_voxel_grid_filter()
LEAF_SIZE = 0.005
vox.set_leaf_size(LEAF_SIZE, LEAF_SIZE, LEAF_SIZE)
cloud_filtered = vox.filter()
filename = 'voxel_downsampled.pcd'
pcl.save(cloud_filtered, filename)

# PassThrough z
passthrough = cloud_filtered.make_passthrough_filter()
passthrough.set_filter_field_name('z')
passthrough.set_filter_limits(0.6, 1.3)
cloud_filtered = passthrough.filter()

# PassThrough x
passthrough = cloud_filtered.make_passthrough_filter()
passthrough.set_filter_field_name('y')
passthrough.set_filter_limits(-0.5, 0.5)
cloud_filtered = passthrough.filter()
filename = 'pass_through_filtered.pcd'
pcl.save(cloud_filtered, filename)

# RANSAC plane segmentation
seg = cloud_filtered.make_segmenter()
seg.set_model_type(pcl.SACMODEL_PLANE)
seg.set_method_type(pcl.SAC_RANSAC)
max_distance = 0.01
seg.set_distance_threshold(max_distance)
inliers, coefficients = seg.segment()

# Extract inliers
extracted_inliers = cloud_filtered.extract(inliers, negative=False)
filename = 'extracted_inliers.pcd'
pcl.save(extracted_inliers, filename)

# Extract outliers
extracted_outliers = cloud_filtered.extract(inliers, negative=True)
filename = 'extracted_outliers.pcd'
pcl.save(extracted_outliers, filename)


# Save pcd for tabletop objects


