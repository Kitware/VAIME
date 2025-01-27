#! /bin/bash

# debugging flag
set -x

# System Deps
./viame/cmake/build_server_ubuntu_deps.sh

# Install CMAKE
./viame/cmake/build_server_linux_cmake.sh

# Update VIAME sub git deps
cd /viame/
git submodule update --init --recursive
mkdir build
cd build 

# Configure Paths [should be removed when no longer necessary by fletch]
export PATH=$PATH:/viame/build/install/bin
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/viame/build/install/lib

source ./viame/cmake/linux_add_internal_py36_paths.sh

# Configure VIAME
cmake ../ -DCMAKE_BUILD_TYPE:STRING=Release \
-DVIAME_BUILD_DEPENDENCIES:BOOL=ON \
-DVIAME_FIXUP_BUNDLE:BOOL=ON \
-DVIAME_ENABLE_BURNOUT:BOOL=OFF \
-DVIAME_ENABLE_CUDA:BOOL=ON \
-DVIAME_ENABLE_CUDNN:BOOL=ON \
-DVIAME_ENABLE_DIVE:BOOL=ON \
-DVIAME_ENABLE_DOCS:BOOL=OFF \
-DVIAME_ENABLE_FFMPEG:BOOL=ON \
-DVIAME_ENABLE_FFMPEG-X264:BOOL=ON \
-DVIAME_ENABLE_GDAL:BOOL=ON \
-DVIAME_ENABLE_FLASK:BOOL=OFF \
-DVIAME_ENABLE_ITK:BOOL=OFF \
-DVIAME_ENABLE_KWANT:BOOL=ON \
-DVIAME_ENABLE_KWIVER:BOOL=ON \
-DVIAME_ENABLE_MATLAB:BOOL=OFF \
-DVIAME_ENABLE_OPENCV:BOOL=ON \
-DVIAME_OPENCV_VERSION:STRING=3.4.0 \
-DVIAME_ENABLE_PYTHON:BOOL=ON \
-DVIAME_PYTHON_BUILD_FROM_SOURCE:BOOL=ON \
-DVIAME_PYTHON_VERSION:STRING=3.10.4 \
-DVIAME_ENABLE_PYTORCH:BOOL=ON \
-DVIAME_PYTORCH_BUILD_FROM_SOURCE:BOOL=ON \
-DVIAME_ENABLE_PYTORCH-MMDET:BOOL=ON \
-DVIAME_ENABLE_PYTORCH-NETHARN:BOOL=ON \
-DVIAME_ENABLE_PYTORCH-PYSOT:BOOL=ON \
-DVIAME_ENABLE_SCALLOP_TK:BOOL=OFF \
-DVIAME_ENABLE_SEAL:BOOL=OFF \
-DVIAME_ENABLE_SMQTK:BOOL=ON \
-DVIAME_ENABLE_TENSORFLOW:BOOL=OFF \
-DVIAME_ENABLE_UW_PREDICTOR:BOOL=OFF \
-DVIAME_ENABLE_VIVIA:BOOL=ON \
-DVIAME_ENABLE_VXL:BOOL=ON \
-DVIAME_ENABLE_DARKNET:BOOL=ON 

# Build VIAME, pipe output to file
../cmake/build_server_linux_build.sh > build_log.txt 2>&1

# Output check statments
if grep -q "Built target viame" build_log.txt; then
  echo "VIAME Build Succeeded"

  # Make zip file of install
  mv install viame
  rm VIAME-v1.0.0-Ubuntu-64Bit.tar.gz ||:
  tar -zcvf VIAME-v1.0.0-Ubuntu-64Bit.tar.gz viame
  mv viame install
else
  echo "VIAME Build Failed"
  exit 1
fi

if  grep -q "fixup_bundle: preparing..." build_log.txt; then
  echo "Fixup Bundle Called Succesfully"
else
  echo "Error: Fixup Bundle Not Called"
  exit 1
fi
