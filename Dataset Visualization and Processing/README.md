## Workflow

1. Managed to run code provided by partho, code runs on google colab, but does not run on kaggle website.

2. Tried image averaging with 10 frames. When averaged over 10 frames, the output image is fairly noise free and gives an overview of the events of those 10 frames.

3. Averaging all frames of the entire clip results in an overall map of blood vessels present in the video file, but there is some loss of important detail. Noise performance is fairly good
![image_1](screenshots/average_effect.png)

4. Noise condition of the images seem to be apparent from the histogram of the frames. In general, images with more noise have a wider histogram, and good images have a narrower histogram. Histogram operations have been tried, but the results are not good. Histogram equalization gave noisier images. Some sort of histogram squeezing has to be done to obtain better lit images
![image_2](screenshots/histogram_analysis.png)

5. Replaced the binary images from partho's training set with averaged grayscale images and trained model. The results are quite poor
	
    - We could try making a 3D map of the blood vessels in the video then use those 3d maps through some 3D convolutional network
    
    - We could sample blood vessels from non ROI locations, and use the samples to train a generative adversarial network. The GAN network will predict how a blood vessel should look like. Say for example, we take blood vessels, and remove some regions from the images - representing blocks. Then we show the edited image,  and teach the network that output should look like the original image when it sees the edited image. The network should be able to learn how to fill the gaps in an image - namely filling up empty spaces. Then when testing with original ROIs, we can ask the network how much the input differs from the predicted image. Larger difference indicates higher chance of block
    
    - Partho suggested that we could build an autoencoder that will do necessary noise removal and brightness correction in any input image. Then the corrected image will be used to train the final stall catching network. For training the autoencoder, we have to manually provide required hyperparameters for each video file that transforms the original video and does the corrections/transformations. Then we have to train the autoencoder on those hyperparameters. This suggestion seems like a reasonable approach. 

6. Did some investigating with pixel intensity values. From the plots of a single row, column or a column taken in direction of depth, the presence of vessels can be observed from concurrent high pixel values. I have an idea for filtering the images with a low pass filter in any one of the three directions.
![image_3](screenshots/pixel_intensity.png)

7. When a 3d array is viewed from the side, the vessels can be seen too, and it can give a rough estimation of depth diffence between consecutive frames.
![image_4](screenshots/side_view.png)

8. Low pass Butterworth filter does not give good results, simple Gaussian Blur would perform better apparently. Will look into 3D filtering techniques.
![image_5](screenshots/filter1D.png)

9. Some reliable progress

    - Import all the video frames > Extract ROIs > 3D Gaussian filter (sigma 1, order 0) > average over 5 frames, in 2 frame interval of start position
    - On the 3D array, find three values for 99, 95, 90 th percentile and apply thresholding on that value over the 3D array. 3 Point clouds are generated
    - In each point cloud, apply DBSCAN clustering, remove any clusters having points less than 1/100th of the largest cluster
    - It is visually possible to classify stalls by comparing the three point clouds
    - It is possible to reverse the point cloud to generate binary images for each layer of the point cloud.

10. Tried <a href="https://www.kaggle.com/daavoo/3d-mnist">MNIST3D</a> example. Exported point clouds for 3 percentile values to .h5 files and generated voxel grid data of size samplesx3x32x64x64 for feeding to the network. Results are not satisfactory yet, and the RAM usage is unsuallay high.

    - Pixel density based analysis
    - Graph CNN
    - 2 way clustering
    - Generative adversarial network
    - Cloud optimization(Voxel grid downsampling, Convex Hull, Cloud to mesh)
    - Fast Marching Algorithm, Snake Algorithm

11. Currently running RESNET3D 18 model, on point cloud data:

    - First attempt was a) Voxel size 32*64*64 b) Validation mcc 0.44 c) Leaderboard mcc 0.2408
    - Second attempt a) Voxel size 32*64*64, normalized voxel 0-1, made some improvement in voxel generation b) Validation mcc 0.49 and very stable during training c) Leaderboard mcc 0.307
    - Third attempt a) Used weights from previous submission as model checkpoint, data volume 4 times by rotation along z axis b) Validation mcc 0.515 c) Leaderboard mcc 0.3716
    - Fourth attempt a) Voxel size 50x128x128 (normalized), training incredibly slow b) Validation mcc 0.328 c) Leaderboard mcc 0.2172
    
12. Partho created a 9 stream network, each stream for a specific angle projection of point cloud depth map. Created the dataset and gave it to Partho

    
### Links
1. Point Cloud Materials
    - http://www.open3d.org/
    - https://docs.scipy.org/doc/scipy/reference/generated/scipy.ndimage.gaussian_filter.html#scipy.ndimage.gaussian_filter
    - https://paperswithcode.com/task/3d-point-cloud-classification
    - https://github.com/charlesq34/pointnet
    - https://github.com/charlesq34/pointnet2
    - https://github.com/WangYueFt/dgcnn
    - https://towardsdatascience.com/5-step-guide-to-generate-3d-meshes-from-point-clouds-with-python-36bad397d8ba

2. 3D convolution
    - https://towardsdatascience.com/step-by-step-implementation-3d-convolutional-neural-network-in-keras-12efbdd7b130
    - https://www.kaggle.com/daavoo/3d-mnist



<!--

Depth min: 10.0 average: 29.342642767819925 max: 91.0
42.0 49.0 67.0
Height min: 12.0 average: 54.506044185077116 max: 384.0
92.0 112.0 160.03999999999996
Width min: 16.0 average: 56.716965402250935 max: 512.0
94.0 116.0 180.03999999999996

-->