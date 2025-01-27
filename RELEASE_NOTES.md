v0.21.0 - 1/15/2024
===================


-Add track scoring metrics


-Updated scoring scripts to support bulk ingest


-Added ability to sweep certain scoring metrics amongst multiple thresholds


-Added a number of improvements for stereo measurement and supporting additional camera formats


-Added segment anything support for box to polygon conversion


-Upgraded default python version in releases from 3.6 to 3.10


-Upgraded torch, opencv, fletch versions to current latest


-Update release CUDA version from 11.3 to 12.4, requires driver updates for some


-Update DIVE interface with some new features (e.g. bulk download, current frame dets only opt)



v0.20.4 - 3/30/2024
===================


-Update DIVE GUI version with a number of new features


-Update default fish detection model


-Add bulk format conversion scripts



v0.20.3 - 12/01/2023
====================


-Fix issue when running metadata-using pipelines on image sequences with more than 6000 files


-Add additional algorithms for Novelty detection


-Update darknet repo and adjust default YOLO architecture and settings


-Default configuration file renaming



v0.20.2 - 08/18/2023
====================


-Updated DIVE version with multi cam utility pipelines and fix for large resolution input


-Fix for running fusion pipelines on large resolution images


-Fix for recently integrated convnext detectors on large resolution images



v0.20.1 - 06/29/2023
====================


-Additional metadata-based measurement techniques added


-Add low-shot learning techniques from the DARPA Learn project


-Add stereo changes from Ifremer project


-Add missed DLL for YOLO on certain windows OS


-Autoconvert detections to full frame labels when training a frame classifier


-Fixed issue in last release with model training on certain configs on linux


-Remove development header files and share folder config files from default binaries



v0.20.0 - 02/10/2023
====================


-Utility pipeline updates: add enhancement utility, retain IDs in remove in regions


-Update DIVE to support large image processing


-Secondary detector refinement and frame classifier training parameter tweaks



v0.19.9 - 02/06/2023
====================


-Updates to support refined scallop measurements


-Additional updates to fusion classifiers



v0.19.8 - 10/30/2022
====================


-Add extra scripts for scoring (confusion matrices, PRC curves)


-Extra classifier options (default back to efficiencynetv2, multi-cat infastructure)


-Update DIVE on Linux



v0.19.7 - 10/17/2022
====================


-Update DIVE GUI with a number of improvements and windows authentication



v0.19.6 - 10/9/2022
===================


-Fix issue with 15hz video downsampled to 15hz and some other derivatives



v0.19.5 - 10/7/2022
===================


-Fix issues in SVM train introduced in v0.19.*


-Fix issues in utility pipelines introduced in last


-Add second watershed segmentation process



v0.19.4 - 7/18/2022
===================


-Fix multi-camera mosaic issue when only < 2 cams succesfully mosaic


-Loop closure option for registration-based tracking and duplicate suppression


-Upgrade YOLOv4-tiny to YOLOv7-tiny


-Extra train video input folder options


-Fix Mask-RCNN test (inference) pipeline running



v0.19.3 - 6/21/2022
===================


-Add extra option for track only frame extraction script


-Extra default YOLO hyperpameter tuning



v0.19.2 - 5/30/2022
===================


-Fix for DIVE multi-camera locked zooming


-Add support for bulk processing multi-camera data in project folders


-Add additional mosaicing helper scripts and examples



v0.19.1 - 5/24/2022
===================


-Sync project folder extract_frames with other downsamplers (web, desktop GUIs)


-Add scripts to prj to chunk long videos into smaller segments


-Add script to extract frames with detections only


-Consolidate image and video project templates


-Update DIVE version in VIAME: multi-cam, checkboxes for right type



v0.19.0 - 5/8/2022
==================


-Update default generic model for IQR


-Update CUDA, torch, mmdet, netharn versions


-Make mmdet/netharn detectors be half disk size (no duplicate weights stored)


-Reduce YOLOv4-CSP model size, parameter tuning


-Allow CPU releases to use all GPU models regardless of type


-Update classifiers from resnet50/resnext101 to efficentnet_v2_s by default



v0.18.2 - 4/9/2022
==================


-Add extra track averaging methods



v0.18.1 - 4/7/2022
==================


-Updated DIVE interface


-Minor tweaks to track moving average type scoring



v0.18.0 - 3/20/2022
===================


-Fix system issue in CFRNN detector train


-Default YOLO parameter tweak



v0.17.9 - 3/2/2022
==================


-Updates to DIVE interface


-Fix frame extract script



v0.17.8 - 2/11/2022
===================


-Fixes to DIVE interface, add track trails


-Fix issues with running multiple user initialized trackers



v0.17.7 - 1/15/2022
===================


-Fix issue in running user-initialized tracking on videos


-Fix issues with reclassifier pipelines on certain datasets


-Fix issue with DIVE and loading certain videos in desktop linux



v0.17.6 - 1/3/2022
==================


-Updated NMS option and fix for detector fusion approaches



v0.17.5 - 12/27/2021
====================


-Updated DIVE for multi-camera pipeline processing and other


-Darknet and netharn resnet parameter tuning


-Fix linux runtime issues if certain version of CUDA 11 locally installed



v0.17.4 - 10/22/2021
====================


-Fix local project folder run in DIVE


-Other config file renames



v0.17.3 - 10/19/2021
====================


-Point project folders to correct YOLO config



v0.17.2 - 10/16/2021
====================


-Support reading polygons in COCO reader



v0.17.1 - 10/15/2021
====================


-Fix runtime issue in refinement process



v0.17.0 - 10/14/2021
====================


-CUDA 10.1 => 11.1


-NetHarn detector updates


-YOLOv3 => v4-CSP


-Update default tracker models


-Updated DIVE interface



v0.16.1 - 7/12/2021
===================


-Updated DIVE interface (Misc)



v0.16.0 - 7/12/2021
===================


-Updated DIVE interface (add stereo pipe support and multi-camera)


-Fix issue in training directly on videos with non-default frame rates



v0.15.2 - 6/04/2021
===================


-Fix issue in exe installer


-Minor update for stabilization example



v0.15.0 - 5/26/2021
===================


-Significant DIVE interface updates and bug fixes


-Updates to stereo measurement process



v0.14.1 - 3/10/2021
===================


-Update DIVE interface


-Updates to classifier refiner process



v0.14.0 - 2/5/2021
==================


-Include DIVE interface in default VIAME installers


-Fix issue in ResNetX classifier still downloading things at inference time


-Fix issue in track averaging of target object types


-Update darknet to include instruction sets for more recent GPUs



v0.13.4 - 2/1/2021
==================


-Updates to support training in the VIAME-DIVE interface



v0.13.3 - 1/27/2021
===================


-Fix error in frame classifier train



v0.13.2 - 1/26/2021
===================


-Fix training error introduced in last in print statements for netharn detectors


-Switch default algorithm and pipeline name for 'wtf' cfrnn variant



v0.13.1 - 1/22/2021
===================


-Update darknet wrapper to allow for non-square input perspective fields


-Add CLI option for no special prints during train for DIVE desktop support


-Fix certain csv downloads from viame web not working on desktop



v0.13.0 - 1/15/2021
===================


-Update several dependencies for faster train: pytorch 1.4->1.7, mmcv, netharn


-Add additional supported training datastructures, input lists


-Add support for training direct on videos, other video support improvements


-Fix issues in videos with dropped frames and incorrect metadata



v0.12.1 - 11/19/2020
====================


-Add new default fish detectors, pipeline renames



v0.12.0 - 10/28/2020
====================


-Improved CFRNN with motion train and test proceedures


-Update NetHarn version


-Improved CFRNN initial learning rate estimations


-Extra support for VIAME-Web train


-Extra warning printouts when training models for possible corner cases



v0.11.3 - 10/14/2020
====================


-Add extra log comments to training log for verifying image reads


-Fix filename parsing in seal-tk GUI for unknown filename types



v0.11.2 - 10/4/2020
===================


-Do not write out polygons when just rectangles drawn in GUI


-Support polys in annotation csv in model training tool


-Support training on folders with no labels.txt present


-Improved CFRNN WTF training pipeline with improved features



v0.11.1 - 9/16/2020
===================


-Upgrade multiple dependencies: pytorch, cuda, nvidia driver, mmdet


-Additional support for full frame classifiers


-Support viame csv for polygon saveout from desktop annotator


-Seal multi-view GUI fix zooming issue, allow scoring editing



v0.10.10 - 7/30/2020
====================


-Fix issue on windows running CFRNN training from pipelines dropdown


-Fix issue in C++ hello world example


-Fix issue in linux running IQR search and rapid model generation



v0.10.9 - 4/30/2020
===================


-Fix issue on windows with running CFRNN detectors at test time


-Fix issue with running detector downloading excess un-needed model files



v0.10.9 - 4/06/2020
===================


-Fix issue with CFRNN training on windows


-Add continue training from prior model CFRNN script


-Fix issue in habcam model pack



v0.10.8 - 3/20/2020
===================


-Fix issue with timeout in latest CFRNN training



v0.10.7 - 3/19/2020
===================


-Fix issue with labels.txt file not being used in latest CFRNN training



v0.10.6 - 3/18/2020
===================


-Fix scoring examples which became broken in last


-Add tracker training example for windows binaries


-Fix issue in running test-time multi-GPU from an image input list


-Add extra checks for project file scripts with early exits



v0.10.5 - 2/26/2020
===================


-Add improved CFRNN training proceedure using netharn



v0.10.4 - 1/31/2020
===================


-Fix issue in centos binaries backing X11 library



v0.10.3 - 1/13/2020
===================


-Refine cascade faster rcnn training proceedure first pass


-Add tracker-assisted annotation for video


-Fix split track option in default annotator


-New seal multi-view GUI release



v0.10.2 - 12/1/2019
===================


-Fix CentOS issues with unable to run pipelines (Ubuntu and Windows fine)



v0.10.2 - 11/25/2019
====================


-Updated KWIVER in VIAME causing all add-ons to break and need to be regenerated


-Added in support for object tracking solely based on IOU and image stabilization


-Fixed issue in installers with measurement code after upgrading numpy versions


-Add simple mosaic generation script and related pipelines


-Add multiple seal tracking example pipelines


-Fix issues in prior v0.10.* releases on systems with no CUDA 10s installed



v0.10.1 - 11/16/2019
====================


-Remove ball-tree indexing in favor of full LSH hash searches due to issues


-Begin packaging python in binaries for linux in addition to windows



v0.10.0 - 11/15/2019
====================


-Baseline speed optimizations and bug fixes for IQR, significant database speedups


-Begin packaging python in binaries for windows, will do this for linux soon



v0.9.18 - 11/01/2019
===================


-Fixed windows issues with running and training detectors introduced in last


v0.9.17 - 10/18/2019
====================


-Quick fixes to make IQR GUI not crash on images of different size and large images


-Add SVM training tool example, for training SVMs from large amounts of annotations


-Misc tuning and bug fixes



v0.9.16 - 7/24/2019
===================


-Lots of bug fixes (windows project files)


-Learning rate tuning for latest detection models


-CUDA 10.0 support



v0.9.13 - 5/30/2019
===================


-Add missing .so files into CentOS and Ubuntu binaries to not require external packages



v0.9.12 - 5/21/2019
===================


-Support local detection running for multiple variants of motion detectors


-All detector training routines now also generate KWIVER pipelines


-Remove index_existing and merged changes into index_defaults to reduce confusion


-Additional detection models



v0.9.11 - 5/16/2019
===================


-New default and generic object detection models


-Improved IQR detector performance


-The default box detector training routine is now cascade rnn instead of yolo



v0.9.10.0 - 4/22/2019
=====================


-New detection techniques and default models: cascade faster rcnn, cfrnn with motion, YOLO-WTF


-Additional support for frame-level classification in the system


-Image registration example added, arctic seal examples



v0.9.9.7 - 3/19/2019
====================


-Fixed a few issues in last relating to detector optimizations which broke things in last


-More intuitive final model saveouts


v0.9.9.6 - 2/25/2019
====================


-Windows 7 runtime training tool fixes


-Better automatic video detection, don't process hidden files, dirs recursively or non-videos


-Show correct time offsets in query GUI from video start


v0.9.9.5 - 2/21/2019
====================


-Fix bug added to deep training tool in last version


-Fix training tool windows error reporting


v0.9.9.4 - 2/18/2019
====================


-Fix model saveout in windows binaries broken in last


-Updated default model training parameters


v0.9.9.3 - 2/13/2019
====================


-Minor python change to drop dependency in standard use case


v0.9.9.2 - 2/12/2019
====================


-Add train deep model from GUI dropdown


v0.9.9.1 - 2/6/2019
===================


-Fix issues in prior release dealing with default indexing option and finding local models


v0.9.9.0 - 2/4/2019
===================


-Add YOLOv3, YOLOv3 with Temporal Features detectors


-GUI bug fixes: issues with running embedded pipes and detections not always showing up


-Configuration file cleanup


-Remove multiple models from default installers, move to seperate .zips



v0.9.8.11 - 12/4/2018
=====================


-Improved timeline plotting for multi-video inputs


-Fixed issue in image list project files introduced in prior


-More intelligent default track classification probabilities which make use of keyframes



v0.9.8.10 - 11/26/2018
======================


-Add automatic dynamic range compute for 16-bit imagery in GUI


-Expose video rate for image list processing in default project files


-Added extra error checking on indexing scripts involving databases, improved error reporting



v0.9.8.9 - 11/12/2018
=====================


-Allow video projects to process directory of directory of images


-Additional error checking on index formation


-Improvements to launch_timeline_viewer script


-Added GUI display dynamic range parameters for 16-bit imagery



v0.9.8.8 - 10/29/2018
=====================


-Fix issue with measurement example after config refactor



v0.9.8.7 - 10/25/2018
=====================


-Additional bug fixes and parameter tuning relating to tile boundaries when chipping enabled in detectors



v0.9.8.6 - 10/24/2018
=====================


-Fixed a bug in debayer and color correction filter .pipe which was causing garbled results in the example


-Added RELEASE_NOTES to binaries


-Fixes to Windows CPU-only binaries


-Fixes for properly processing greyscale imagery


-Non-maximum suppression tuning


-If there is a corrupt frame in the middle of a sequence, keep on processing in both GUI and CLI



v0.9.8.5 - 10/18/2018
=====================


-Improved video support in default project file run scripts


-Configuration files have been refactored and their structured cleaned up


-Additional annotation GUI embedded pipelines added, directory structure improved
