#! /bin/bash

# debugging flag
set -x

# Fletch, VIAME, CMAKE system deps
./viame/cmake/build_server_ubuntu_deps.sh

# Install CMAKE
./viame/cmake/build_server_linux_cmake.sh

# Update VIAME sub git deps
cd /viame/
git submodule update --init --recursive
mkdir build
cd build

# Add VIAME and CUDA paths to build
export PATH=$PATH:/usr/local/cuda/bin:/viame/build/install/bin
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/viame/build/install/lib:/usr/local/cuda/lib64

# Configure VIAME
cmake ../ -DCMAKE_BUILD_TYPE:STRING=Release \
-DVIAME_BUILD_DEPENDENCIES:BOOL=ON \
-DVIAME_FIXUP_BUNDLE:BOOL=OFF \
-DVIAME_VERSION_RELEASE:BOOL=ON \
-DVIAME_ENABLE_BURNOUT:BOOL=OFF \
-DVIAME_ENABLE_CUDA:BOOL=ON \
-DVIAME_ENABLE_CUDNN:BOOL=ON \
-DVIAME_ENABLE_DARKNET:BOOL=ON \
-DVIAME_ENABLE_DIVE:BOOL=OFF \
-DVIAME_ENABLE_DOCS:BOOL=OFF \
-DVIAME_ENABLE_FFMPEG:BOOL=ON \
-DVIAME_ENABLE_FFMPEG-X264:BOOL=ON \
-DVIAME_ENABLE_GDAL:BOOL=OFF \
-DVIAME_ENABLE_FLASK:BOOL=OFF \
-DVIAME_ENABLE_ITK:BOOL=OFF \
-DVIAME_ENABLE_KWANT:BOOL=OFF \
-DVIAME_ENABLE_KWIVER:BOOL=ON \
-DVIAME_ENABLE_LEARN:BOOL=ON \
-DVIAME_ENABLE_MATLAB:BOOL=OFF \
-DVIAME_ENABLE_OPENCV:BOOL=ON \
-DVIAME_OPENCV_VERSION:STRING=3.4.0 \
-DVIAME_ENABLE_PYTHON:BOOL=ON \
-DVIAME_PYTHON_BUILD_FROM_SOURCE:BOOL=OFF \
-DVIAME_ENABLE_PYTORCH:BOOL=ON \
-DVIAME_PYTORCH_BUILD_FROM_SOURCE:BOOL=ON \
-DVIAME_PYTORCH_VERSION:STRING=2.5.1 \
-DVIAME_PYTORCH_DISABLE_NINJA=ON \
-DVIAME_ENABLE_PYTORCH-MMDET:BOOL=ON \
-DVIAME_ENABLE_PYTORCH-NETHARN:BOOL=ON \
-DVIAME_ENABLE_PYTORCH-PYSOT:BOOL=ON \
-DVIAME_ENABLE_SCALLOP_TK:BOOL=OFF \
-DVIAME_ENABLE_SEAL:BOOL=OFF \
-DVIAME_ENABLE_SMQTK:BOOL=ON \
-DVIAME_ENABLE_TENSORFLOW:BOOL=OFF \
-DVIAME_ENABLE_UW_PREDICTOR:BOOL=OFF \
-DVIAME_ENABLE_VIVIA:BOOL=OFF \
-DVIAME_ENABLE_VXL:BOOL=ON \
-DVIAME_ENABLE_WEB_EXCLUDES:BOOL=ON \
-DVIAME_DOWNLOAD_MODELS:BOOL=ON \
-DVIAME_DOWNLOAD_MODELS-PYTORCH:BOOL=ON \
-DVIAME_DOWNLOAD_MODELS-ARCTIC-SEAL:BOOL=OFF \
-DVIAME_DOWNLOAD_MODELS-HABCAM:BOOL=OFF \
-DVIAME_DOWNLOAD_MODELS-MOUSS:BOOL=OFF

# Perform multi-threaded build
make -j$(nproc) > build_log.txt 2>&1 || true

# Below be krakens
# (V) (°,,,°) (V)   (V) (°,,,°) (V)   (V) (°,,,°) (V)

# HACK: Ensure invalid libsvm symlink isn't created
# Should be removed when this issue is fixed
rm install/lib/libsvm.so
cp install/lib/libsvm.so.2 install/lib/libsvm.so

# Remove all source files used for the build to save space and mode
# viame install to default linux install location
if [ -f "install/setup_viame.sh" ]; then
  cd /viame/build
  rm build_log.txt
  mkdir /opt/noaa
  mv install viame
  mv viame /opt/noaa
  cd /
  rm -rf /viame
  chown -R 1099:1099 /opt/noaa/viame
fi
  
