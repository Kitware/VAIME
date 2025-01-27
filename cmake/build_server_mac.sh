#! /bin/bash

# Activate python environment
source /Users/kitware/miniconda3/bin/activate

# Update VIAME sub git sources
export VIAME_SOURCE_FOLDER=/Users/kitware/Jenkins/workspace/VIAME-MacOS-CPU-Release
export VIAME_BUILD_FOLDER=${VIAME_SOURCE_FOLDER}/build
export VIAME_INSTALL_FOLDER=${VIAME_BUILD_FOLDER}/install

cd $VIAME_SOURCE_FOLDER
git submodule update --init --recursive
mkdir $VIAME_BUILD_FOLDER
cd $VIAME_BUILD_FOLDER

# Configure Paths [should be removed when no longer necessary by fletch]
export PATH=$PATH:$VIAME_INSTALL_FOLDER/bin
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$VIAME_INSTALL_FOLDER/lib

# Configure VIAME
cmake ../ -DCMAKE_BUILD_TYPE:STRING=Release \
-DVIAME_BUILD_DEPENDENCIES:BOOL=ON \
-DVIAME_FIXUP_BUNDLE:BOOL=ON \
-DVIAME_DISABLE_PYTHON_CHECKS:BOOL=ON \
-DVIAME_ENABLE_BURNOUT:BOOL=OFF \
-DVIAME_ENABLE_CUDA:BOOL=OFF \
-DVIAME_ENABLE_CUDNN:BOOL=OFF \
-DVIAME_ENABLE_DIVE:BOOL=ON \
-DVIAME_ENABLE_DOCS:BOOL=OFF \
-DVIAME_ENABLE_FFMPEG:BOOL=ON \
-DVIAME_ENABLE_GDAL:BOOL=OFF \
-DVIAME_ENABLE_FLASK:BOOL=OFF \
-DVIAME_ENABLE_ITK:BOOL=OFF \
-DVIAME_ENABLE_KWANT:BOOL=ON \
-DVIAME_ENABLE_KWIVER:BOOL=ON \
-DVIAME_ENABLE_MATLAB:BOOL=OFF \
-DVIAME_ENABLE_OPENCV:BOOL=ON \
-DVIAME_OPENCV_VERSION:STRING=3.4.0 \
-DVIAME_ENABLE_PYTHON:BOOL=ON \
-DVIAME_PYTHON_BUILD_FROM_SOURCE:BOOL=OFF \
-DVIAME_ENABLE_PYTORCH:BOOL=ON \
-DVIAME_PYTORCH_BUILD_FROM_SOURCE:BOOL=OFF \
-DVIAME_ENABLE_PYTORCH-MMDET:BOOL=OFF \
-DVIAME_ENABLE_PYTORCH-NETHARN:BOOL=OFF \
-DVIAME_ENABLE_PYTORCH-PYSOT:BOOL=OFF \
-DVIAME_ENABLE_SCALLOP_TK:BOOL=OFF \
-DVIAME_ENABLE_SEAL:BOOL=OFF \
-DVIAME_ENABLE_SMQTK:BOOL=OFF \
-DVIAME_ENABLE_TENSORFLOW:BOOL=OFF \
-DVIAME_ENABLE_UW_PREDICTOR:BOOL=OFF \
-DVIAME_ENABLE_VIVIA:BOOL=OFF \
-DVIAME_ENABLE_VXL:BOOL=ON \
-DVIAME_ENABLE_DARKNET:BOOL=ON 

# Build VIAME first attempt
make -j$(nproc) -k || true

# Below be krakens
# (V) (°,,,°) (V)   (V) (°,,,°) (V)   (V) (°,,,°) (V)

# HACK: Copy mac python environment to installer
cp -r /Users/kitware/miniconda3 install

# HACK: Double tap the build tree
# Should be removed when non-determinism in kwiver python build fixed
make -j$(nproc)

# HACK: Copy setup_viame.sh.install over setup_viame.sh
# Should be removed when this issue is fixed
cp ../cmake/setup_viame.sh.install install/setup_viame.sh

# HACK: Ensure invalid libsvm symlink isn't created
# Should be removed when this issue is fixed
rm install/lib/libsvm.so
cp install/lib/libsvm.so.2 install/lib/libsvm.so

