#!/bin/bash

# Path to VIAME installation
export VIAME_INSTALL=/opt/noaa/viame

# Core processing options
export INPUT_DIRECTORY=training_data
export DEFAULT_ANNOTATION_FRAME_RATE=5.0

# Setup paths and run command
source ${VIAME_INSTALL}/setup_viame.sh

# Adjust log level
export KWIVER_DEFAULT_LOG_LEVEL=info

viame_train_detector \
  -i ${INPUT_DIRECTORY} \
  -c ${VIAME_INSTALL}/configs/pipelines/train_detector_netharn_cfrnn_motion.viame_csv.conf \
  --threshold 0.0 --default-vfr ${DEFAULT_ANNOTATION_FRAME_RATE}
