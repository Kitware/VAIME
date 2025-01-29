#!/bin/sh

# Path to VIAME installation
export VIAME_INSTALL="$(cd "$(dirname ${BASH_SOURCE[0]})" && pwd)/../.."

source ${VIAME_INSTALL}/setup_viame.sh

# Adjust log level
export KWIVER_DEFAULT_LOG_LEVEL=info

# Run pipeline
viame_train_detector \
  -i training_data_sea_lion \
  -c ${VIAME_INSTALL}/configs/pipelines/train_detector_netharn_mask_rcnn_720.conf \
  --threshold 0.0
