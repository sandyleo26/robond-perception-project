## Project: Perception Pick & Place

---

Here I will consider the [rubric points](https://review.udacity.com/#!/rubrics/1067/view) individually and describe how I addressed each point in my implementation.  

[//]: # (Image reference)
[world3]: ./images/world3.png
[passthrough]: ./images/passthrough.png
[outlier]: ./images/outlier.png
[cluster]: ./images/cluster.png
[confusion_nonormal]: ./images/confusion_nonormal.png
[confusion_normal]: ./images/confusion_normal.png
[world1_rviz]: ./images/world1_rviz.png
[world2_rviz]: ./images/world2_rviz.png
[world3_rviz]: ./images/world3_rviz.png

### 1. Writeup / README

> Provide a Writeup / README that includes all the rubric points and how you addressed each one.  You can submit your writeup as markdown or pdf.  

You're reading it!

### 2. Exercise 1, 2 and 3 pipeline implemented
> 1. Complete Exercise 1 steps. Pipeline for filtering and RANSAC plane fitting implemented.

The pipeline in this stage is summerized as below.

1. **Statistical Outlier Filtering**. This is to filter out noisy data. Here `k = 20` and `x = 0.3`
2. **Voxel Grid Downsampling**. This is to reduce point cloud size. Here `LEAF_SIZE = 0.005`
3. **PassThrough Filter**. This is to take out only the region of interst. On `z` axis, the range is `(0.6, 1.3)`; on `y` axis, the range is `(-0.5, 0.5)`
4. **RANSAC Plane Segmentation**. This is to segment the table and objects above. Here `max_distance = 0.01`
5. **Extract inliers and outliers**. This is a follow-up to the previous step to extract point indices. Here inlier is table and outlier are objects

The parameters are fine tuned based on experiments using an adapted `RANSAC.py` borrowed from Excercise-1. This is because working on a point cloud dump could provide me feedback for the pipeline much faster than seeing the results in RViz. Since the environment in this project is different than that in the excercise, I modified the code to dump a point cloud from test world 3. Some snapshots below.

Original cloud dump. (We can see that there're ~640k points)
![Point cloud dump from world 3][world3]

After passthrough.(Now reduced to ~25k)
![After passthrough][passthrough]

Outlier(objects).(Only 8k now)
![Extracted outlier][outlier]


> Complete Exercise 2 steps: Pipeline including clustering for segmentation implemented.  

The pipeline in this stage is summerised as below.

1. **Euclidean Clustering**. This is to cluster points based on their neighbouring points. Here tolerance is `0.015`, min cluster is `20`, max cluster is `3000`
2. **Create Cluster-Mask Point Cloud**. This is simply for visualizing each cluster

In this stage, it's quite time consuming to fine tune those parameters as it needs to launch Gazebo and RViz, which is really slow on my laptop. I come up with these numbers based on my experiments and others' in the forum.

Snapshot of clustering in test world 2.
![Test world 2 clustering][cluster]


> Complete Exercise 3 Steps. Features extracted and SVM trained. Object recognition implemented.

This step can be summerized as below.
1. The training environment is borrowed directly from sensor_stick. The `capture_features.py` from sensor_stick is modified to have all the models used in this project.
2. `100` samples are generated for each model. This gives a good accuracy but still makes generating time managable (~40 min)
3. The features used are same as those in excercises. `HSV` is used since it gives better result. `32` bins are used for both color and normal histograms. The range for color histogram is `(0, 256)` while it's `(-1, 1)` for normal. 
4. Same SVM parameters are used in excercise.

This is the confusion matrix. The overall acccuracy is 0.96. 
![Without normal][confusion_nonormal]

![Normal][confusion_normal]



### 3. Pick and Place Setup

> For all three tabletop setups (`test*.world`), perform object recognition, then read in respective pick list (`pick_list_*.yaml`). Next construct the messages that would comprise a valid `PickPlace` request output them to `.yaml` format.

In this stage, it's mainly constructing the yaml file for each 3 world. The steps are:

1. For all points in a cluster identified above, extract features using `compute_color_histograms` and `compute_normal_histograms`
2. Use the saved model to predicd based on the extracted features
3. Make marker labels and add the detected object in a list
1. Retrieve `dropbox` and `object_list` parameters for later use
2. Loop through the detected objects:
3. Check if the object is in the pick list; If not, issue a warning message
	
		for do in detected_objects:
        		matched_object = None
        		for object in object_list_param:
            	if do.label == object['name']:
              	matched = True
              	matched_object = object
              	break
        
        		if matched_object == None:
            		rospy.loginfo('No detected object found for {}'.format(do.label))
            		
4. Assign `test_scene_num`, `arm_name`, `object_name`, `pick_pose` and `place_pose`. The centroid is calculated as in the lecture. The `pick_pose` is the object's centroid; the `place_pose` is from corresponding dropbox name for the object's group

		# pick_pose
		points_arr = ros_to_pcl(do.cloud).to_array()
		pick_pose = Pose()
		m = np.mean(points_arr, axis=0)[:3]
		pick_pose.position.x = np.asscalar(m[0])
		pick_pose.position.y = np.asscalar(m[1])
		pick_pose.position.z = np.asscalar(m[2])
		
		# place_pose
		place_pose = Pose()
		dropbox = green_dropbox_position if matched_object['group'] == 'green' else red_dropbox_position
		place_pose.position.x = dropbox[0]
		place_pose.position.y = dropbox[1]
		place_pose.position.z = dropbox[2]

5. `yaml` dict is constructed using `make_yaml_dict` and appended to a list, which is later dumped in the `output_*` file.

The following are snapshots for each test world.

Test world 1
![world 1][world1_rviz]

Test world 2
![world 2][world2_rviz]

Test world 3
![world 3][world3_rviz]

Discussions about the result:

1. All 3 objects are successfully recognized in world 1; 4 out of 5 objects in world 2; and 8 out of 8 in world 3.

2. For world 2, the missing one is glue, which is most of the time recognized as biscuits. It's quite a surprise given their different shape and color. However, the other time it does successfully recognize it as glue (as shown in _Complete Exercise 2 step_ above)

3. For world 3, most of time all 8 objects can be recognized however, sometime the `eraser` will be recognized as `soap2`. This again struck me as a little surprise given their color difference.

4. The filtering and clustering stages are key to recognition, even with higher accuracy. It make sense in that the training is done on noise-free samples so unless certain steps are taken (e.g. training data augmentation), the model's generalization ability over noisy input will not be very good. 

5. Simply increasing training dataset could lead to further better accuracy. I've seen others generating 1000+ samples for each model but I'm afraid that'll burn my laptop. Also dataset could be added with noise just like before filtering

6. Also worth to consider is to add more [features](http://cs229.stanford.edu/proj2015/171_report.pdf) besides color and normals. 


### 4. Future work
0. Improve performance on world 2 and 3
1. try the model in tabletop_challenge.world
2. PR2 Collision Avoidance
3. accomplish the pick and place task