
kwiver_create_python_init( arrows/pytorch )

if( VIAME_ENABLE_PYTORCH-MMDET )
  kwiver_add_python_module(
    ${CMAKE_CURRENT_SOURCE_DIR}/mmdet_compatibility.py
    arrows/pytorch
    mmdet_compatibility )

  kwiver_add_python_module(
    ${CMAKE_CURRENT_SOURCE_DIR}/mmdet_detector.py
    arrows/pytorch
    mmdet_detector )

  kwiver_add_python_module(
    ${CMAKE_CURRENT_SOURCE_DIR}/mmdet_trainer.py
    arrows/pytorch
    mmdet_trainer )

  kwiver_add_python_module(
    ${CMAKE_CURRENT_SOURCE_DIR}/mmdet_launcher.py
    arrows/pytorch
    mmdet_launcher )

endif()

# Common Utilities
kwiver_add_python_module(
  ${CMAKE_CURRENT_SOURCE_DIR}/_utils.py
  arrows/pytorch
  _utils )

kwiver_add_python_module(
  ${CMAKE_CURRENT_SOURCE_DIR}/kwcoco_train_detector.py
  arrows/pytorch
  kwcoco_train_detector )

if( VIAME_ENABLE_PYTORCH-NETHARN )

  kwiver_add_python_module(
    ${CMAKE_CURRENT_SOURCE_DIR}/netharn_classifier.py
    arrows/pytorch
    netharn_classifier )

  kwiver_add_python_module(
    ${CMAKE_CURRENT_SOURCE_DIR}/netharn_detector.py
    arrows/pytorch
    netharn_detector )

  kwiver_add_python_module(
    ${CMAKE_CURRENT_SOURCE_DIR}/netharn_trainer.py
    arrows/pytorch
    netharn_trainer )

  kwiver_add_python_module(
    ${CMAKE_CURRENT_SOURCE_DIR}/netharn_refiner.py
    arrows/pytorch
    netharn_refiner )

  kwiver_add_python_module(
    ${CMAKE_CURRENT_SOURCE_DIR}/netharn_utils.py
    arrows/pytorch
    netharn_utils )

endif()

if( VIAME_ENABLE_PYTORCH-MIT-YOLO )
  kwiver_add_python_module(
    ${CMAKE_CURRENT_SOURCE_DIR}/mit_yolo_trainer.py
    arrows/pytorch
    mit_yolo_trainer )
endif()

if( VIAME_ENABLE_PYTORCH-MDNET )

  add_subdirectory( mdnet )

  kwiver_add_python_module(
    ${CMAKE_CURRENT_SOURCE_DIR}/mdnet_tracker.py
    arrows/pytorch
    mdnet_tracker )

  kwiver_add_python_module(
    ${CMAKE_CURRENT_SOURCE_DIR}/mdnet_tracker_process.py
    processes/pytorch
    mdnet_tracker_process )

endif()

if( VIAME_ENABLE_LEARN )

  add_subdirectory( cutler )
  add_subdirectory( remax )

  kwiver_add_python_module(
    ${CMAKE_CURRENT_SOURCE_DIR}/remax_convnext_detector.py
    arrows/pytorch
    remax_convnext_detector )

  kwiver_add_python_module(
    ${CMAKE_CURRENT_SOURCE_DIR}/remax_convnext_trainer.py
    arrows/pytorch
    remax_convnext_trainer )

  kwiver_add_python_module(
      ${CMAKE_CURRENT_SOURCE_DIR}/remax_dino_detector.py
      arrows/pytorch
      remax_dino_detector )

  kwiver_add_python_module(
      ${CMAKE_CURRENT_SOURCE_DIR}/remax_dino_trainer.py
      arrows/pytorch
      remax_dino_trainer )


endif()
