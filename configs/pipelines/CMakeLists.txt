###
# Download and install enabled model files
##
if( VIAME_DOWNLOAD_MODELS )

  # Default fish detection model
  if( VIAME_DOWNLOAD_MODELS-FISH )
    if( VIAME_ENABLE_PYTORCH-NETHARN )
      DownloadAndExtract(
        https://data.kitware.com/api/v1/item/660a2e5aaa5c8de3874c4160/download
        22dacdc4afc2956406cf13d44ae51408
        ${VIAME_DOWNLOAD_DIR}/models-netharn_fish-v1.6.zip
        ${CMAKE_CURRENT_SOURCE_DIR} )
    elseif( VIAME_ENABLE_PYTORCH-MMDET )
      DownloadAndExtract(
        https://data.kitware.com/api/v1/item/5fb196f250a41e3d1956a407/download
        c6e0cdf1e903dbe3e261977378a97223
        ${VIAME_DOWNLOAD_DIR}/models-mmdet_default-v1.4.tar.gz
        ${CMAKE_CURRENT_SOURCE_DIR} )
    elseif( VIAME_ENABLE_DARKNET )
      DownloadAndInstallAddOn(
        https://viame.kitware.com/api/v1/item/6172423562e0e5717e22cc21/download
        5b8a947d4d9de3ecc7acd8e729652ada
        ${VIAME_DOWNLOAD_DIR}/VIAME-Default-CPU-Detectors-v1.0.zip )
    endif()
  endif()

  # Generic object detection model
  if( VIAME_DOWNLOAD_MODELS-GENERIC )
    if( VIAME_ENABLE_DARKNET )
      DownloadAndExtract(
        https://data.kitware.com/api/v1/item/626e05b54acac99f425acc46/download
        72fe8f6cc1653b350154e32d03efd6c0
        ${VIAME_DOWNLOAD_DIR}/models-yolo_generic-v1.5.zip
        ${CMAKE_CURRENT_SOURCE_DIR} )
    elseif( VIAME_ENABLE_PYTORCH-NETHARN )
      DownloadAndExtract(
        https://data.kitware.com/api/v1/item/62682a514acac99f420f6883/download
        c71f276ac893502803504dad10150cc8
        ${VIAME_DOWNLOAD_DIR}/models-netharn_generic-v1.4.zip
        ${CMAKE_CURRENT_SOURCE_DIR} )
    elseif( VIAME_ENABLE_PYTORCH-MMDET )
      DownloadAndExtract(
        https://data.kitware.com/api/v1/item/5fb1922650a41e3d1956a389/download
        bf2df19944c55e8a7dc757520c607893
        ${VIAME_DOWNLOAD_DIR}/models-mmdet_generic-v1.4.tar.gz
        ${CMAKE_CURRENT_SOURCE_DIR} )
    endif()
  endif()

  # SAM2 generic segmentation model
  if( VIAME_ENABLE_PYTORCH-SAM )
    DownloadAndExtract(
      https://data.kitware.com/api/v1/item/6757401e9ccf870f61ceacb9/download
      54958fe7a3a0fdb8f831d89cc5bc0a69
      ${VIAME_DOWNLOAD_DIR}/models-sam2_v1.0.zip
      ${CMAKE_CURRENT_SOURCE_DIR} )
  endif()

  # Motion detection model
  if( VIAME_DOWNLOAD_MODELS-MOTION )
    if( VIAME_ENABLE_PYTORCH-NETHARN )
      DownloadAndInstallAddOn(
        https://viame.kitware.com/api/v1/item/627b326fea630db5587b577b/download
        eff47c8693b936514cc98674a2c0c3b7
        ${VIAME_DOWNLOAD_DIR}/VIAME-Motion-Models-v1.0.zip )
    endif()
  endif()

  # Other PyTorch detection, tracking, and training (seed) models
  if( VIAME_ENABLE_PYTORCH )

    # Seed models for model training
    if( VIAME_ENABLE_PYTORCH-NETHARN OR VIAME_ENABLE_PYTORCH-MMDET )
      DownloadAndExtract(
        https://data.kitware.com/api/v1/item/5fb1922d50a41e3d1956a396/download
        d1befaf3b64c185f40a29ed2fca87929
        ${VIAME_DOWNLOAD_DIR}/models-mmdet_primitives-v1.4.tar.gz
        ${CMAKE_CURRENT_SOURCE_DIR} )
    endif()

    # Default annotation assist tracking models
    if( VIAME_ENABLE_PYTORCH-PYSOT )
      DownloadAndExtract(
        https://viame.kitware.com/api/v1/item/61e4e0ebe90592181da06a79/download
        39c2a4de745edbed0452f8e951c57537
        ${VIAME_DOWNLOAD_DIR}/models-pysot_tracking_models-v1.2.zip
        ${CMAKE_CURRENT_SOURCE_DIR} )
    endif()

    if( VIAME_ENABLE_PYTORCH-MDNET )
      DownloadAndExtract(
        https://data.kitware.com/api/v1/item/5e12b04aaf2e2eed35d42979/download
        8f6a709478bbd69e4d97fc34ac9b6003
        ${VIAME_DOWNLOAD_DIR}/models-mdnet_tracking_models-v1.0.0.tar.gz
        ${CMAKE_CURRENT_SOURCE_DIR} )
    endif()

    # Default multi-target tracking models
    DownloadAndExtract(
      https://data.kitware.com/api/v1/item/5facb1bb50a41e3d194d2af6/download
      eb66d389e7fd58529b5cd4b00d6b5058
      ${VIAME_DOWNLOAD_DIR}/models-pytorch_tracking-v1.2.0.tar.gz
      ${CMAKE_CURRENT_SOURCE_DIR} )

    # Default descriptor models
    DownloadAndExtract(
      https://data.kitware.com/api/v1/item/62d4dc10bddec9d0c45560b9/download
      c2a966ee5b48cb123ff6e3739c00b9bf
      ${VIAME_DOWNLOAD_DIR}/models-pytorch_descriptors-v1.3.zip
      ${CMAKE_CURRENT_SOURCE_DIR} )
  endif()

  # Darknet training seed models
  if( VIAME_ENABLE_DARKNET )
    DownloadAndExtract(
      https://data.kitware.com/api/v1/item/65697428c5a2b36857ad1a0a/download
      80cfe1dfd89ccd938b587a81b13bdef9
      ${VIAME_DOWNLOAD_DIR}/models-yolo_v4_csp_s_seed_model-v1.0.zip
      ${CMAKE_CURRENT_SOURCE_DIR} )
  endif()

  # Caffe generic descriptor
  if( VIAME_ENABLE_CAFFE )
    DownloadAndExtract(
      https://data.kitware.com/api/v1/item/5afe6e1e8d777f15ebe1d6fc/download
      2cdbe7ca51b49b12e59911aadec20e98
      ${VIAME_DOWNLOAD_DIR}/models-default_caffe_descriptor-v1.0.0.tar.gz
      ${CMAKE_CURRENT_SOURCE_DIR} )
  endif()
endif()

###
# All config files manually-included by default or based on options
##
set( CORE_PIPELINE_FILES
  classify_detections_svm.pipe
  common_default_initializer.pipe
  common_default_input.pipe
  common_default_input_with_downsampler.pipe
  common_fish_detector.pipe
  common_fish_detector_with_filter.pipe
  common_generic_detector.pipe
  common_generic_detector_with_filter.pipe
  common_image_stabilizer.pipe
  common_measurement_gmm_stereo_track_fish.pipe
  common_no_load_input.pipe
  common_no_load_input_with_downsampler.pipe
  common_stabilized_iou_tracker.pipe
  common_stereo_input.pipe
  common_stereo_input_with_downsampler.pipe
  convert_add_filename_to_det_csv.pipe
  convert_add_filename_to_trk_csv.pipe
  convert_coco_json_to_viame_csv.pipe
  convert_habcam_to_kw18.pipe
  convert_habcam_to_viame_csv.pipe
  convert_kw18_to_viame_csv.pipe
  convert_to_onnx.pipe
  convert_oceaneyes_to_viame_csv.pipe
  convert_viame_csv_to_coco_json.pipe
  convert_viame_csv_to_kw18.pipe
  database_apply_svm_models.pipe
  detector_camtrawl.pipe
  detector_fish_without_motion.pipe
  detector_generic_proposals.pipe
  detector_project_folder.pipe
  detector_project_folder_left.pipe
  detector_simple_hough.pipe
  detector_svm_models.pipe
  display_annotations.pipe
  filter_debayer.pipe
  filter_debayer_and_enhance.pipe
  filter_default.pipe
  filter_draw_dets.pipe
  filter_enhance.pipe
  filter_split_and_debayer.pipe
  filter_split_left_side.pipe
  filter_split_right_side.pipe
  filter_stereo_depth_map.pipe
  filter_to_kwa.pipe
  filter_to_video.pipe
  filter_tracks_only.pipe
  frame_classifier_project_folder.pipe
  frame_classifier_svm.pipe
  index_default.pipe
  index_default.svm.pipe
  index_default.trk.pipe
  index_existing.pipe
  index_fish.svm.pipe
  index_frame.pipe
  index_frame.svm.pipe
  index_frame.svm.annot_only.pipe
  measurement_default.trk.pipe
  measurement_gmm_only.pipe
  query_image_exemplar.cfe.pipe
  query_image_exemplar.pipe
  query_retrieval_and_iqr.cfe.pipe
  query_retrieval_and_iqr.pipe
  query_video_exemplar.pipe
  sql_init_table.sql
  tracker_fish.pipe
  tracker_generic.pipe
  tracker_project_folder.pipe
  tracker_stabilized_iou.pipe
  tracker_svm_models.pipe
  train_aug_add_color_freq.pipe
  train_aug_add_double_motion.pipe
  train_aug_add_motion_and_color_freq.pipe
  train_aug_add_motion.pipe
  train_aug_enhance_and_add_motion.pipe
  train_aug_hue_shifting_only.pipe
  train_aug_intensity_color_freq_motion.pipe
  train_aug_intensity_hue_motion.pipe
  train_aug_motion_only.pipe
  train_aug_split_and_stereo.pipe
  train_aug_split.pipe
  train_aug_warp_ir_to_eo.pipe
  transcode_default.pipe
  transcode_draw_dets.pipe
  transcode_compress.pipe
  transcode_enhance.pipe
  transcode_tracks_only.pipe
  utility_add_head_tail_keypoints.pipe
  utility_add_segmentations_watershed.pipe
  utility_add_segmentations_watershed_2x.pipe
  utility_debayer_and_enhance.pipe
  utility_empty_frame_lbls_1fr.pipe
  utility_empty_frame_lbls_10fr.pipe
  utility_empty_frame_lbls_100fr.pipe
  utility_empty_frame_lbls_1000fr.pipe
  utility_enhance.pipe
  utility_extract_chips.pipe
  utility_link_detections_default.pipe
  utility_max_10_points_per_poly.pipe
  utility_max_25_points_per_poly.pipe
  utility_remove_dets_in_ignore_regions.pipe
  utility_register_frames.pipe
  utility_register_frames_2-cam.pipe
  utility_register_frames_3-cam.pipe )

# Configs which differ based on CPU vs GPU
if( VIAME_ENABLE_CUDA )
  set( CORE_PIPELINE_FILES ${CORE_PIPELINE_FILES}
    common_default_descriptor.pipe
    common_default_tracker.pipe
    common_fish_detector.pipe
    common_stereo_fish_detector_with_filter.pipe
    common_stereo_fish_detector.pipe
    common_generic_detector.pipe
    measurement_gmm_stereo_detect_fish.pipe
    measurement_gmm_stereo_track_fish.pipe
    query_augment_image.pipe
    tracker_fish.sfd.pipe )
else()
  install( FILES common_default_descriptor.cpu.pipe
    DESTINATION configs/pipelines
    RENAME common_default_descriptor.pipe )
  install( FILES common_default_tracker.cpu.pipe
    DESTINATION configs/pipelines
    RENAME common_default_tracker.pipe )
  install( FILES query_augment_image.cpu.pipe
    DESTINATION configs/pipelines
    RENAME query_augment_image.pipe )
  install( FILES tracker_fish.sfd.cpu.pipe
    DESTINATION configs/pipelines
    RENAME tracker_fish.sfd.pipe )
endif()

# Pytorch specific configs
if( VIAME_ENABLE_PYTORCH )
  set( CORE_PIPELINE_FILES ${CORE_PIPELINE_FILES}
    train_detector_default.conf
    train_frame_classifier_default.conf
    train_reclassifier_default.conf )
endif()

# Darknet specific configs
if( VIAME_ENABLE_DARKNET )
  set( CORE_PIPELINE_FILES ${CORE_PIPELINE_FILES}
    train_detector_darknet_yolo_default.conf
    train_detector_darknet_yolo_640.conf
    train_detector_darknet_yolo_640.grid_only.conf
    train_detector_darknet_yolo_640.no_grid.conf
    train_detector_darknet_yolo_704.habcam.conf
    train_detector_darknet_yolo_704.kw18.conf
    train_detector_darknet_yolo_full_res.no_grid.conf )
endif()

# Configs used exclusively for VIEW
if( VIAME_ENABLE_VIVIA )
  set( GUI_PIPELINE_FILES
    embedded_single_stream/filter_debayer.pipe
    embedded_single_stream/filter_debayer_and_enhance.pipe
    embedded_single_stream/filter_enhance.pipe
    embedded_single_stream/fish_detector_without_motion.pipe
    embedded_single_stream/fish_tracker.pipe
    embedded_single_stream/generate_empty_frame_lbls_0001fr.pipe
    embedded_single_stream/generate_empty_frame_lbls_0010fr.pipe
    embedded_single_stream/generate_empty_frame_lbls_0100fr.pipe
    embedded_single_stream/generate_empty_frame_lbls_1000fr.pipe
    embedded_single_stream/generic_proposal_detector.pipe
    embedded_single_stream/generic_proposal_tracker.pipe
    embedded_single_stream/local_deep_detector.pipe
    embedded_single_stream/local_deep_detector_with_def_tracker.pipe
    embedded_single_stream/local_deep_detector_with_stab_tracker.pipe
    embedded_single_stream/local_svm_detector.pipe
    embedded_single_stream/local_svm_detector_with_def_tracker.pipe
    embedded_single_stream/local_svm_frame_classifier.pipe )

  if( VIAME_ENABLE_DARKNET )
    set( GUI_PIPELINE_FILES ${GUI_PIPELINE_FILES}
      embedded_single_stream/train_deep_detector_yolo.pipe )
  endif()

  if( VIAME_ENABLE_PYTORCH )
    set( GUI_PIPELINE_FILES ${GUI_PIPELINE_FILES}
      embedded_single_stream/train_deep_detector_cfrnn.pipe )
  endif()

  if( VIAME_ENABLE_PYTORCH AND VIAME_ENABLE_PYTORCH-PYSOT )
    set( GUI_PIPELINE_FILES ${GUI_PIPELINE_FILES}
      embedded_single_stream/track_user_selections_fast.pipe )

    if( VIAME_ENABLE_PYTORCH-MDNET )
      set( GUI_PIPELINE_FILES ${GUI_PIPELINE_FILES}
        embedded_single_stream/track_user_selections_fusion.pipe )
    endif()
  endif()

  install( FILES       ${GUI_PIPELINE_FILES}
           DESTINATION configs/pipelines/embedded_single_stream )
endif()

if( VIAME_ENABLE_BURNOUT )
  set( CORE_PIPELINE_FILES ${CORE_PIPELINE_FILES}
    burnout_det_descriptor.cfe.conf
    burnout_det_descriptors.conf
    burnout_enhancement.conf
    burnout_trk_descriptor.cfe.conf
    burnout_trk_descriptors.conf
    burnout_pixel_classification.conf
    burnout_pixel_detection.conf
    burnout_train_classifier.conf
    detector_burnout.pipe
    filter_burnout.pipe )
endif()

if( VIAME_ENABLE_SMQTK )
  set( CORE_PIPELINE_FILES ${CORE_PIPELINE_FILES}
    smqtk_compute_hashes.json
    smqtk_desc_index.json
    smqtk_make_balltree.json
    smqtk_nn_index.json
    smqtk_postgres_ingest.json
    smqtk_query.pipe
    smqtk_train_itq.json
    train_detector_svm_over_fish_detections.conf
    train_detector_svm_over_generic_detections.conf
    train_frame_classifier_libsvm_svm.conf )
endif()

if( VIAME_ENABLE_OPENCV )
  set( CORE_PIPELINE_FILES ${CORE_PIPELINE_FILES}
    register_using_homographies.pipe
    register_multimodal_unsync_ocv.pipe
    detector_ocv_target.pipe
    tracker_ocv_target.pipe
    measurement_gmm_stereo_track_ocv_target.pipe
    measurement_gmm_stereo_rectified_disparity.pipe
    measurement_gmm_stereo_track_fish_3d_from_detections_and_rectified_disparity.pipe
    measurement_gmm_stereo_calibrate_cameras.pipe
    measurement_gmm_calibrate_cameras.pipe
    )
endif()

if( VIAME_ENABLE_PYTORCH AND VIAME_ENABLE_PYTORCH-MMDET )
#  set( CORE_PIPELINE_FILES ${CORE_PIPELINE_FILES}
#    train_detector_mmdet_cfrnn.habcam.conf
#    train_detector_mmdet_cfrnn.conf)
endif()

if( VIAME_ENABLE_PYTORCH AND VIAME_ENABLE_PYTORCH-SAM )
  set( CORE_PIPELINE_FILES ${CORE_PIPELINE_FILES}
    utility_add_segmentations_default.pipe
    utility_add_segmentations_sam2.pipe )
endif()

if( VIAME_ENABLE_PYTORCH-NETHARN )
  set( CORE_PIPELINE_FILES ${CORE_PIPELINE_FILES}
    train_detector_netharn_cfrnn.conf
    train_detector_netharn_cfrnn.grid_only.conf
    train_detector_netharn_cfrnn.grid_only.20ep.conf
    train_detector_netharn_cfrnn.grid_only.40ep.conf
    train_detector_netharn_cfrnn.continue.conf
    train_detector_netharn_cfrnn.habcam.conf
    train_detector_netharn_cfrnn_motion.conf
    train_detector_netharn_cfrnn_special.conf
    train_detector_netharn_cfrnn_wtf.conf
    train_detector_netharn_mask_rcnn_720.conf
    train_detector_netharn_mask_rcnn_1280.conf
    train_detector_netharn_mask_rcnn_grid.conf
    train_frame_classifier_netharn_efficientnet.conf
    train_frame_classifier_netharn_efficientnet.continue.conf
    train_frame_classifier_netharn_resnet.conf
    train_frame_classifier_netharn_resnet.continue.conf
    train_reclassifier_netharn_efficientnet.conf
    train_reclassifier_netharn_resnet.conf )
endif()

if( VIAME_ENABLE_PYTORCH AND VIAME_ENABLE_PYTORCH-PYSOT )
  set( CORE_PIPELINE_FILES ${CORE_PIPELINE_FILES}
    common_short_term_tracker.pipe
    utility_track_selections_default_mask.pipe
    utility_track_selections_fish_box_only.pipe )
endif()

if( VIAME_ENABLE_ITK )
  set( CORE_PIPELINE_FILES ${CORE_PIPELINE_FILES}
    register_multimodal_sync_itk.pipe
    register_multimodal_unsync_itk.pipe )
endif()

if( VIAME_ENABLE_MATLAB )
  set( CORE_PIPELINE_FILES ${CORE_PIPELINE_FILES}
    detector_matlab_camtrawl.pipe )
endif()

if( VIAME_ENABLE_CAFFE )
  set( CORE_PIPELINE_FILES ${CORE_PIPELINE_FILES}
    tracker_fish.sfd.cfe.pipe
    index_default.sfd.cfe.pipe )
endif()

if( VIAME_ENABLE_SEAL OR VIAME_DOWNLOAD_MODELS-ARCTIC-SEAL )
  set( DUAL_EMBEDDED_FILES
    embedded_dual_stream/local_trained_eo_detector.pipe
    embedded_dual_stream/local_trained_ir_detector.pipe )

  if( VIAME_ENABLE_PYTORCH-NETHARN )
    set( DUAL_EMBEDDED_FILES ${DUAL_EMBEDDED_FILES}
      embedded_dual_stream/train_cfrnn_eo.pipe
      embedded_dual_stream/train_cfrnn_ir.pipe )
  endif()

  if( VIAME_ENABLE_DARKNET )
    set( DUAL_EMBEDDED_FILES ${DUAL_EMBEDDED_FILES}
      embedded_dual_stream/train_yolo_eo.pipe
      embedded_dual_stream/train_yolo_ir.pipe )
  endif()

  if( VIAME_ENABLE_PYTORCH-PYSOT )
    set( DUAL_EMBEDDED_FILES ${DUAL_EMBEDDED_FILES}
      embedded_dual_stream/track_user_selections_fast.pipe )
  endif()

  install( FILES       ${DUAL_EMBEDDED_FILES}
           DESTINATION configs/pipelines/embedded_dual_stream )
endif()

###
# Perform actual installation steps
##
if( VIAME_ENABLE_WEB_EXCLUDES )
  set( VIAME_WEB_FILES_TO_IGNORE
    classify_detections_svm.pipe
    database_apply_svm_models.pipe
    detector_project_folder.pipe
    detector_project_folder_left.pipe
    detector_simple_hough.pipe
    detector_svm_models.pipe
    frame_classifier_project_folder.pipe
    frame_classifier_svm.pipe
    tracker_project_folder.pipe
    tracker_svm_models.pipe
    utility_add_head_tail_keypoints.pipe
    utility_enhance.pipe
    utility_extract_chips.pipe
    train_detector_darknet_yolo_704.habcam.conf
    train_detector_darknet_yolo_704.kw18.conf
    train_detector_darknet_yolo_full_res.no_grid.conf
    train_detector_netharn_cfrnn.continue.conf
    train_detector_netharn_cfrnn.habcam.conf
    train_detector_netharn_cfrnn_special.conf
    train_detector_netharn_cfrnn_wtf.conf
    train_frame_classifier_netharn_efficientnet.continue.conf
    train_frame_classifier_netharn_resnet.continue.conf )

  foreach( ITEM ${VIAME_WEB_FILES_TO_IGNORE} )
    list( REMOVE_ITEM CORE_PIPELINE_FILES "${ITEM}" )
  endforeach()
endif()

###
# Perform actual installation steps
##
install( FILES       ${CORE_PIPELINE_FILES}
         DESTINATION configs/pipelines )
install( DIRECTORY   templates
         DESTINATION configs/pipelines )

if( VIAME_DOWNLOAD_MODELS )
  install( DIRECTORY   models
           DESTINATION configs/pipelines )

  if( VIAME_DOWNLOAD_MODELS-ARCTIC-SEAL )
    install( DIRECTORY   transformations
             DESTINATION configs/pipelines )
  endif()
endif()
