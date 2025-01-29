@echo off

REM Path to VIAME installation
SET VIAME_INSTALL=.\..\..

CALL "%VIAME_INSTALL%\setup_viame.bat"

REM Adjust log level
SET KWIVER_DEFAULT_LOG_LEVEL=info

REM Run pipeline
viame_train_detector.exe ^
  -i training_data_mouss ^
  -c "%VIAME_INSTALL%/configs/pipelines/train_detector_darknet_yolo_704.kw18.conf" ^
  --threshold 0.0

pause
