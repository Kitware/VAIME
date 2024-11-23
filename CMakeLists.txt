###    (V) (°,,,°) (V)     <><     (V) (°,,,°) (V)    <><     (V) (°,,,°) (V)
# Top-level CMakeLists.txt build file for the VIAME super-build and project
##  ) (V)    <><     (V) (°,,,°) (V)     <><     (V) (°,,,°) (V)    <><

cmake_minimum_required( VERSION 3.13.0 )
set( CMAKE_CXX_STANDARD 17 )

project( VIAME )

###
# Core versioning flags
##

set( VIAME_VERSION_MAJOR 1 )
set( VIAME_VERSION_MINOR 0 )
set( VIAME_VERSION_PATCH 0 )

set( VIAME_VERSION "${VIAME_VERSION_MAJOR}.${VIAME_VERSION_MINOR}.${VIAME_VERSION_PATCH}" )

###
# Add global cmake properties
##
include( CMakeDependentOption )

if( POLICY CMP0053 )
  cmake_policy( SET CMP0053 NEW )
endif()

if( POLICY CMP0074 )
  cmake_policy( SET CMP0074 NEW )
endif()

###
# Add script folders for cmake functions
##
list( INSERT CMAKE_MODULE_PATH 0
      "${CMAKE_CURRENT_SOURCE_DIR}/cmake"
      "${KWIVER_CMAKE_DIR}" )

###
# Add other common paths usable throughout all CMakeLists files
##
set( VIAME_SOURCE_DIR               "${CMAKE_SOURCE_DIR}" )
set( VIAME_CMAKE_DIR                "${CMAKE_SOURCE_DIR}/cmake" )
set( VIAME_BINARY_DIR               "${CMAKE_BINARY_DIR}/build" )
set( VIAME_BUILD_PREFIX             "${CMAKE_BINARY_DIR}/build" )
set( VIAME_PACKAGES_DIR             "${VIAME_SOURCE_DIR}/packages" )
set( VIAME_PATCHES_DIR              "${VIAME_PACKAGES_DIR}/patches" )
set( VIAME_DOWNLOAD_DIR             "${VIAME_PACKAGES_DIR}/downloads" )

###
# Add paths which control the output directories of all final install files
#
# When in super-build mode, everything is 'make installed' into these directories
# at build time ('make') instead of at ('make install') time due to the nature
# of cmake super-builds.
##
set( VIAME_BUILD_INSTALL_PREFIX     "${CMAKE_BINARY_DIR}/install"
     CACHE STRING                   "Installation directory to place all final output files" )
mark_as_advanced( VIAME_BUILD_INSTALL_PREFIX )

set( VIAME_INSTALL_PREFIX           "${VIAME_BUILD_INSTALL_PREFIX}"
     CACHE INTERNAL                 "Synonym for VIAME_BUILD_INSTALL_PREFIX" FORCE )
set( CMAKE_INSTALL_PREFIX           "${VIAME_BUILD_INSTALL_PREFIX}"
     CACHE INTERNAL                 "Synonym for VIAME_BUILD_INSTALL_PREFIX" FORCE )

###
# GPU and FFMPEG utilization flags used across projects
##
option( VIAME_ENABLE_CUDA           "Enable CUDA-Dependent Code"    ON )
option( VIAME_ENABLE_CUDNN          "Enable CUDNN-Dependent Code"   ON )
option( VIAME_ENABLE_FFMPEG         "Enable FFMPEG-Dependent Code"  ON )

###
# Add core utilities enable flags
##
option( VIAME_ENABLE_DOCS           "Enable Documentation"          OFF )
option( VIAME_ENABLE_VIVIA          "Enable Vivia GUIs"             OFF )
option( VIAME_ENABLE_SEAL           "Enable Seal GUI"               OFF )
option( VIAME_ENABLE_DIVE           "Enable DIVE GUI"               ON )
option( VIAME_ENABLE_KWANT          "Enable KW Scoring Code"        ON )

mark_as_advanced( VIAME_ENABLE_SEAL )

###
# Add default-enabled algorithmic plugin enable flags
##
option( VIAME_ENABLE_VXL            "Enable VXL plugins"            ON )
option( VIAME_ENABLE_OPENCV         "Enable OpenCV plugins"         ON )
option( VIAME_ENABLE_PYTHON         "Enable Python plugins"         ON )
option( VIAME_ENABLE_PYTORCH        "Enable PyTorch plugins"        ON )
option( VIAME_ENABLE_DARKNET        "Enable Darknet (YOLO) plugin"  ON )

###
# Add secondary plugin enable flags (non-advanced)
##
option( VIAME_ENABLE_MATLAB         "Enable Matlab plugins"         OFF )
option( VIAME_ENABLE_TENSORFLOW     "Enable TensorFlow plugins"     OFF )
option( VIAME_ENABLE_TENSORRT       "Enable TensorRT plugins"       OFF )
option( VIAME_ENABLE_SMQTK          "Enable SMQTK plugins"          ON )

###
# Add secondary plugin enable flags (advanced)
##
option( VIAME_ENABLE_BURNOUT        "Enable Burn-Out plugins"       OFF )
option( VIAME_ENABLE_CAFFE          "Enable Caffe plugins"          OFF )
option( VIAME_ENABLE_GDAL           "Enable GDAL image source"      OFF )
option( VIAME_ENABLE_ITK            "Enable ITK plugins"            OFF )
option( VIAME_ENABLE_KEYPOINTGUI    "Enable Keypoint GUI"           OFF )
option( VIAME_ENABLE_LEARN          "Enable LEARN plugins"          OFF )
option( VIAME_ENABLE_POSTGRESQL     "Enable PostgreSQL plugins"     OFF )
option( VIAME_ENABLE_SCALLOP_TK     "Enable ScallopTK plugin"       OFF )
option( VIAME_ENABLE_UW_PREDICTOR   "Enable UW predictor plugin"    OFF )

if( WIN32 )
  option( VIAME_ENABLE_WIN32GUI     "Enable WIN32 GUI dependency"   ON )
endif()

mark_as_advanced( VIAME_ENABLE_BURNOUT )
mark_as_advanced( VIAME_ENABLE_CAFFE )
mark_as_advanced( VIAME_ENABLE_GDAL )
mark_as_advanced( VIAME_ENABLE_ITK )
mark_as_advanced( VIAME_ENABLE_KEYPOINTGUI )
mark_as_advanced( VIAME_ENABLE_LEARN )
mark_as_advanced( VIAME_ENABLE_VIAME_ENABLE_POSTGRESQL )
mark_as_advanced( VIAME_ENABLE_SCALLOP_TK )
mark_as_advanced( VIAME_ENABLE_UW_PREDICTOR )

if( WIN32 )
  mark_as_advanced( VIAME_ENABLE_WIN32GUI )
endif()

###
# Flags relating to examples and model downloads
##
option( VIAME_INSTALL_EXAMPLES      "Install existing VIAME examples"     ON )
option( VIAME_DOWNLOAD_MODELS       "Download example detection models"   ON )

if( VIAME_DOWNLOAD_MODELS )
  option( VIAME_DOWNLOAD_MODELS-GENERIC     "Download generic proposer models"   ON )
  option( VIAME_DOWNLOAD_MODELS-FISH        "Download default fish models"       ON )
  option( VIAME_DOWNLOAD_MODELS-MOTION      "Download motion detection models"   OFF )
  option( VIAME_DOWNLOAD_MODELS-HABCAM      "Download habcam detection models"   OFF )
  option( VIAME_DOWNLOAD_MODELS-MOUSS       "Download mouss detection models"    OFF )
  option( VIAME_DOWNLOAD_MODELS-ARCTIC-SEAL "Download seal detection models"     OFF )
  option( VIAME_DOWNLOAD_MODELS-IFREMER     "Download ifremer detection models"  OFF )
  option( VIAME_DOWNLOAD_MODELS-SEA-LION    "Download sea lion detection models" OFF )
  option( VIAME_DOWNLOAD_MODELS-CONVNEXT    "Download convnext low-shot models"  OFF )
  option( VIAME_DOWNLOAD_MODELS-POOLCAR     "Download poolcar low-shot models"   OFF )

  mark_as_advanced( VIAME_DOWNLOAD_MODELS-GENERIC )
  mark_as_advanced( VIAME_DOWNLOAD_MODELS-FISH )
  mark_as_advanced( VIAME_DOWNLOAD_MODELS-MOTION )
  mark_as_advanced( VIAME_DOWNLOAD_MODELS-HABCAM )
  mark_as_advanced( VIAME_DOWNLOAD_MODELS-MOUSS )
  mark_as_advanced( VIAME_DOWNLOAD_MODELS-ARCTIC-SEAL )
  mark_as_advanced( VIAME_DOWNLOAD_MODELS-IFREMER )
  mark_as_advanced( VIAME_DOWNLOAD_MODELS-SEA-LION )
  mark_as_advanced( VIAME_DOWNLOAD_MODELS-CONVNEXT )
  mark_as_advanced( VIAME_DOWNLOAD_MODELS-POOLCAR )
else()
  set( VIAME_DOWNLOAD_MODELS-GENERIC     OFF CACHE BOOL "Forced off" FORCE )
  set( VIAME_DOWNLOAD_MODELS-FISH        OFF CACHE BOOL "Forced off" FORCE )
  set( VIAME_DOWNLOAD_MODELS-MOTION      OFF CACHE BOOL "Forced off" FORCE )
  set( VIAME_DOWNLOAD_MODELS-HABCAM      OFF CACHE BOOL "Forced off" FORCE )
  set( VIAME_DOWNLOAD_MODELS-MOUSS       OFF CACHE BOOL "Forced off" FORCE )
  set( VIAME_DOWNLOAD_MODELS-ARCTIC-SEAL OFF CACHE BOOL "Forced off" FORCE )
  set( VIAME_DOWNLOAD_MODELS-IFREMER     OFF CACHE BOOL "Forced off" FORCE )
  set( VIAME_DOWNLOAD_MODELS-SEA-LION    OFF CACHE BOOL "Forced off" FORCE )
  set( VIAME_DOWNLOAD_MODELS-CONVNEXT    OFF CACHE BOOL "Forced off" FORCE )
  set( VIAME_DOWNLOAD_MODELS-POOLCAR     OFF CACHE BOOL "Forced off" FORCE )
endif()

###
# Additional libraries built on pytorch and versioning
##
if( VIAME_ENABLE_PYTORCH )
  set( VIAME_PYTORCH_VERSION 1.13.1 CACHE STRING "PyTorch version to use" )
  set_property( CACHE VIAME_PYTORCH_VERSION PROPERTY STRINGS "1.10.2" "1.11.0" "1.13.1" )
  mark_as_advanced( VIAME_PYTORCH_VERSION )

  set( PYTORCH_INTERNAL_VERSION 1.10.2 CACHE INTERNAL "Internal pytorch version" )

  option( VIAME_ENABLE_PYTORCH-INTERNAL     "Enable internal PyTorch build" OFF )
  option( VIAME_ENABLE_PYTORCH-VIS-INTERNAL "Enable internal TorchVision"   ON )
  option( VIAME_ENABLE_PYTORCH-SEGMENT-ANY  "Enable segment PyTorch code"   OFF )
  option( VIAME_ENABLE_PYTORCH-VIDEO        "Enable video PyTorch code"     OFF )
  option( VIAME_ENABLE_PYTORCH-MMDET        "Enable mmdet PyTorch code"     ON )
  option( VIAME_ENABLE_PYTORCH-NETHARN      "Enable netharn PyTorch code"   ON )
  option( VIAME_ENABLE_PYTORCH-PYSOT        "Enable pysot PyTorch code"     OFF )
  option( VIAME_ENABLE_PYTORCH-DETECTRON    "Enable detectron PyTorch code" OFF )
  option( VIAME_ENABLE_PYTORCH-MDNET        "Enable mdnet PyTorch code"     OFF )

  mark_as_advanced( VIAME_ENABLE_PYTORCH-INTERNAL )
  mark_as_advanced( VIAME_ENABLE_PYTORCH-VIS-INTERNAL )
  mark_as_advanced( VIAME_ENABLE_PYTORCH-SEGMENT-ANY )
  mark_as_advanced( VIAME_ENABLE_PYTORCH-VIDEO )
  mark_as_advanced( VIAME_ENABLE_PYTORCH-MMDET )
  mark_as_advanced( VIAME_ENABLE_PYTORCH-NETHARN )
  mark_as_advanced( VIAME_ENABLE_PYTORCH-PYSOT )
  mark_as_advanced( VIAME_ENABLE_PYTORCH-DETECTRON )
  mark_as_advanced( VIAME_ENABLE_PYTORCH-MDNET )
endif()

###
# Additional libraries built on tensorflow and versioning
##
if( VIAME_ENABLE_TENSORFLOW )
  set( VIAME_TENSORFLOW_VERSION 2.6.0 CACHE STRING "Tensorflow version to use" )
  set_property( CACHE VIAME_TENSORFLOW_VERSION PROPERTY STRINGS "1.14.0" "2.6.0" )
  mark_as_advanced( VIAME_TENSORFLOW_VERSION )

  option( VIAME_ENABLE_TENSORFLOW-MODELS "Enable TensorFlow models repo"   ON )
endif()

###
# Additional libraries built for ffmpeg
##
if( VIAME_ENABLE_FFMPEG )
  option( VIAME_ENABLE_FFMPEG-X264 "Enable libx264 codec in FFmpeg" ON )
  option( VIAME_ENABLE_FFMPEG-X265 "Enable libx265 codec in FFmpeg" ON )
  option( VIAME_ENABLE_FFMPEG-FFNV "Enable ffnv codec in FFmpeg"    OFF )
  mark_as_advanced( VIAME_ENABLE_FFMPEG-X264 )
  mark_as_advanced( VIAME_ENABLE_FFMPEG-X265 )
  mark_as_advanced( VIAME_ENABLE_FFMPEG-FFNV )
endif()

###
# Core build settings advanced flags
##

# Alternative build directories for specific components
set( VIAME_BUILD_KWIVER_DIR "${VIAME_BUILD_PREFIX}/src/kwiver-build"
     CACHE STRING "VIAME superbuild KWIVER build location" )
mark_as_advanced( VIAME_BUILD_KWIVER_DIR )

set( VIAME_BUILD_PLUGINS_DIR "${VIAME_BUILD_PREFIX}/src/viame-build"
     CACHE STRING "VIAME superbuild plugins build location" )
mark_as_advanced( VIAME_BUILD_PLUGINS_DIR )

# If VIAME_FORCEBUILD is False, we will assume we dont need to rebuild any
# other superbuild projects (except for viame). This makes development builds
# much quicker if just doing development only in VIAME plugins if OFF.
option( VIAME_FORCEBUILD "Enable force-building of all subpackages" ON )
mark_as_advanced( VIAME_FORCEBUILD )

# Should we build a version of python within VIAME itself
option( VIAME_ENABLE_PYTHON-INTERNAL "Build python within VIAME"    OFF )
mark_as_advanced( VIAME_ENABLE_PYTHON-INTERNAL )

###
# Other advanced hidden flags used for disabling core features
#
# These are meant for use by advanced users when you only want to use VIAME
# to build one of the above packages by itself, not VIAME core.
##
option( VIAME_ENABLE_KWIVER         "Enable KWIVER pipelining"      ON )
option( VIAME_ENABLE_VIAME_PLUGINS  "Enable VIAME plugins"          ON )

mark_as_advanced( VIAME_ENABLE_KWIVER )
mark_as_advanced( VIAME_ENABLE_VIAME_PLUGINS )

# A continuation build allows building of new plugins using an existing
# VIAME build in another folder or build tree, for the purpose of making
# chained windows MSI installers
option( VIAME_PACKAGING_CONT_BUILD  "Enable continuation build"     OFF )
mark_as_advanced( VIAME_PACKAGING_CONT_BUILD )

if( VIAME_PACKAGING_CONT_BUILD )
  set( VIAME_PRIOR_BUILD "" CACHE PATH "Location of prior VIAME build" )
  mark_as_advanced( VIAME_PRIOR_BUILD )
endif()

###
# Add macro-level package build options
##
option( VIAME_BUILD_DEPENDENCIES    "Build all required dependencies in a super-build" ON )

option( VIAME_FIXUP_BUNDLE          "Run fixup bundle on top of generated binaries"    OFF )
mark_as_advanced( VIAME_FIXUP_BUNDLE )

option( VIAME_CREATE_INSTALLER      "Build a msi prototype installer using wix"        OFF )
mark_as_advanced( VIAME_CREATE_INSTALLER )

option( VIAME_VERSION_RELEASE       "Install release scripts instead of development"   OFF )
mark_as_advanced( VIAME_VERSION_RELEASE )

if( VIAME_CREATE_INSTALLER )
  set( VIAME_FIXUP_BUNDLE ON CACHE BOOL "Flag forced due to create_package enable"     FORCE )
endif()

if( VIAME_FIXUP_BUNDLE )
  set( VIAME_VERSION_RELEASE ON CACHE BOOL "Flag forced due to fixup_bundle enable"    FORCE )
endif()

###
# Add extra options
##
option( VIAME_BUILD_CORE_IMAGE_LIBS "Build core image libraries such as libtiff and libjpeg" ON )
mark_as_advanced( VIAME_BUILD_CORE_IMAGE_LIBS )

option( VIAME_BUILD_TESTS "Build VIAME and all sub-packages with tests enabled"        OFF )
mark_as_advanced( VIAME_BUILD_TESTS )

option( VIAME_BUILD_CHECKS   "Enable version checks on gcc and python"                 ON )
mark_as_advanced( VIAME_BUILD_CHECKS )

###
# Helper macros used across all cmakelists files in this project
##
include( common_macros )
include( old_version_checks )

###
# Add logic and error checking relating to enable flags
##
if( VIAME_ENABLE_CAFFE OR VIAME_ENABLE_SCALLOP_TK OR VIAME_ENABLE_BURNOUT OR
    VIAME_ENABLE_DARKNET )
  set( VIAME_ENABLE_OPENCV  ON CACHE BOOL "OpenCV required for other projects"  FORCE )
endif()

if( VIAME_ENABLE_KWANT OR VIAME_ENABLE_BURNOUT OR VIAME_ENABLE_VIVIA OR
    VIAME_ENABLE_ITK )
  set( VIAME_ENABLE_VXL     ON CACHE BOOL "VXL required for other projects"     FORCE )
endif()

if( VIAME_ENABLE_SMQTK OR VIAME_ENABLE_PYTORCH OR VIAME_ENABLE_TENSORFLOW OR
    VIAME_ENABLE_SEAL )
  set( VIAME_ENABLE_PYTHON  ON CACHE BOOL "Python required for other projects"  FORCE )
endif()

if( VIAME_ENABLE_LEARN )
  set( VIAME_ENABLE_PYTORCH-DETECTRON  ON CACHE BOOL "Detectron required for project" FORCE )
  set( VIAME_ENABLE_PYTORCH-VIDEO      ON CACHE BOOL "Torch Video required for project" FORCE )
endif()

if( VIAME_ENABLE_SMQTK )
  set( VIAME_ENABLE_POSTGRESQL  ON CACHE BOOL "PostgreSQL required for project" FORCE )
endif()

if( VIAME_ENABLE_PYTORCH-VIDEO )
  set( VIAME_ENABLE_FFMPEG  ON CACHE BOOL "FFMpeg required for project" FORCE )
endif()

if( VIAME_ENABLE_MATLAB )
  find_package( Matlab REQUIRED COMPONENTS ENG_LIBRARY MX_LIBRARY )
endif()

if( VIAME_ENABLE_DOCS )
  find_package( Doxygen REQUIRED )
endif()

if( VIAME_ENABLE_VIVIA AND VIAME_ENABLE_SEAL )
  message( FATAL_ERROR "Cannot enable both VIVIA and Seal-TK GUIs" )
endif()

if( VIAME_ENABLE_VIAME_PLUGINS AND NOT VIAME_ENABLE_KWIVER )
  message( FATAL_ERROR "Building core VIAME plugins require KWIVER" )
endif()

if( VIAME_ENABLE_LEARN AND NOT VIAME_ENABLE_CUDA )
  message( FATAL_ERROR "CUDA required for LEARN project currently" )
endif()

if( VIAME_ENABLE_KEYPOINTGUI AND NOT VIAME_ENABLE_PYTHON )
  message( FATAL_ERROR "KEYPOINTGUI requires Python" )
endif()

if( WIN32 AND VIAME_BUILD_DEPENDENCIES AND VIAME_ENABLE_KWIVER AND VIAME_BUILD_CHECKS )
  string( LENGTH "${VIAME_BUILD_KWIVER_DIR}" KWIVER_BUILD_DIR_LENGTH )
  string( LENGTH "${VIAME_BUILD_PLUGINS_DIR}" PLUGINS_BUILD_DIR_LENGTH )

  if( KWIVER_BUILD_DIR_LENGTH GREATER 12 OR PLUGINS_BUILD_DIR_LENGTH GREATER 12 )
    message( FATAL_ERROR "VIAME_BUILD_KWIVER_DIR and VIAME_BUILD_PLUGINS_DIR \
      must be set to a short path (e.g. C:\\tmp\\kv1 and C:\\tmp\\vm1) on \
      Windows due to a current issue with nesting KWIVER exceeding the 260 \
      character default filepath size. Alternatively disable VIAME_BUILD_CHECKS \
      to ignore this message if you either increased the windows default path \
      length, or think your build path is short enough." )
  endif()
endif()

# Check for compilers with only partial C++17 support
if( CMAKE_CXX_COMPILER_ID STREQUAL "GNU" AND
    CMAKE_CXX_COMPILER_VERSION VERSION_LESS "9.0" )
  link_libraries( stdc++fs )
endif()

# Check CUDA related paths
if( VIAME_ENABLE_CUDA )
  find_package( CUDA QUIET REQUIRED )

  if( CUDA_VERSION_MAJOR GREATER_EQUAL 10 AND NOT CUDA_cublas_device_LIBRARY )
    set( CUDA_cublas_device_LIBRARY CACHE INTERNAL "${CUDA_cublas_LIBRARY}" )
  endif()

  if( NOT CUDA_VERSION_PATCH )
    if( CUDA_NVCC_EXECUTABLE AND
        CUDA_NVCC_EXECUTABLE STREQUAL CMAKE_CUDA_COMPILER AND
        CMAKE_CUDA_COMPILER_VERSION MATCHES [=[([0-9]+)\.([0-9]+)\.([0-9]+)]=] )
      set( CUDA_VERSION_PATCH "${CMAKE_MATCH_3}" )
    elseif( CUDA_NVCC_EXECUTABLE )
      execute_process( COMMAND ${CUDA_NVCC_EXECUTABLE} "--version" OUTPUT_VARIABLE NOUT )
      if( NOUT MATCHES [=[ V([0-9]+)\.([0-9]+)\.([0-9]+)]=] )
        set( CUDA_VERSION_PATCH "${CMAKE_MATCH_3}" )
      endif()
    endif()
  endif()

  if( CUDA_VERSION VERSION_EQUAL "10.1" AND CUDA_VERSION_PATCH EQUAL "168" )
    message( FATAL_ERROR "CUDA 10.1.168 has bugs, upgrade to 10.1.264 or above" )
  endif()

  if( CUDA_VERSION_MAJOR GREATER_EQUAL "10" AND VIAME_ENABLE_CAFFE )
    message( FATAL_ERROR "Caffe does not support CUDA 10 or above" )
  endif()

  if( CUDA_VERSION_MAJOR VERSION_LESS "10" AND VIAME_ENABLE_DARKNET )
    message( FATAL_ERROR "Darknet does not support CUDA versions under v10.0" )
  endif()

  option( VIAME_FORCE_CUDA_CSTD98 "Build all cuda code with C++ standard 98" FALSE )
  mark_as_advanced( VIAME_FORCE_CUDA_CSTD98 )

  set( DEF_CUDA_ARCHS "3.5 5.0 5.2 6.0 6.1" )
  if( CUDA_VERSION VERSION_GREATER "8.5" )
    set( DEF_CUDA_ARCHS "${DEF_CUDA_ARCHS} 7.0" )
    if( CUDA_VERSION VERSION_LESS "10.1" )
      set( DEF_CUDA_ARCHS "${DEF_CUDA_ARCHS} 7.0+PTX" )
    endif()
  endif()
  if( CUDA_VERSION VERSION_GREATER "9.5" )
    set( DEF_CUDA_ARCHS "${DEF_CUDA_ARCHS} 7.5" )
    if( CUDA_VERSION VERSION_LESS "11.0" )
      set( DEF_CUDA_ARCHS "${DEF_CUDA_ARCHS} 7.5+PTX" )
    endif()
  endif()
  if( CUDA_VERSION VERSION_GREATER "10.5" )
    set( DEF_CUDA_ARCHS "${DEF_CUDA_ARCHS} 8.0" )
    if( CUDA_VERSION VERSION_LESS "11.1" )
      set( DEF_CUDA_ARCHS "${DEF_CUDA_ARCHS} 8.0+PTX" )
    endif()
  endif()
  if( CUDA_VERSION VERSION_GREATER "11.0" )
    set( DEF_CUDA_ARCHS "${DEF_CUDA_ARCHS} 8.6" )
    if( CUDA_VERSION VERSION_LESS "12.1" )
      set( DEF_CUDA_ARCHS "${DEF_CUDA_ARCHS} 8.6+PTX" )
    endif()
  endif()

  set( CUDA_ARCHITECTURES "${DEF_CUDA_ARCHS}" CACHE STRING "CUDA Architectures" )
  mark_as_advanced( CUDA_ARCHITECTURES )

  if( WIN32 )
    set( VIAME_EXECUTABLES_PATH
      ${VIAME_BUILD_INSTALL_PREFIX}/bin;${CUDA_TOOLKIT_ROOT_DIR}/bin;$ENV{PATH}
      CACHE INTERNAL "All compiled and system-related runnable executables" )
  else()
    set( VIAME_EXECUTABLES_PATH
      ${VIAME_BUILD_INSTALL_PREFIX}/bin:${CUDA_TOOLKIT_ROOT_DIR}/bin:$ENV{PATH}
      CACHE INTERNAL "All compiled and system-related runnable executables" )
  endif()

  if( VIAME_BUILD_CHECKS AND CMAKE_COMPILER_IS_GNUCC AND
      CMAKE_CXX_COMPILER_VERSION VERSION_GREATER 12.0 )
    message( FATAL_ERROR "GCC 12.0+ support is experimental and may not work. "
      "To disable this warning, set VIAME_BUILD_CHECKS to FALSE." )
  endif()

  if( CMAKE_COMPILER_IS_GNUCC AND
      CMAKE_CXX_COMPILER_VERSION VERSION_GREATER 12.0 AND
      CUDA_VERSION VERSION_LESS "11.6" )
    message( FATAL_ERROR "If using GCC 12.0 or greater, enable CUDA 11.7 or "
      "greater, alongside pytorch 1.12 or greater unless you know enough to "
      "hack around this requirement and disable this error." )
  endif()
else()
  set( VIAME_FORCE_CUDA_CSTD98 CACHE INTERNAL FALSE )
  set( CUDA_ARCHITECTURES "" CACHE INTERNAL "CUDA Architectures" )

  if( WIN32 )
    set( VIAME_EXECUTABLES_PATH
      ${VIAME_BUILD_INSTALL_PREFIX}/bin;$ENV{PATH}
      CACHE INTERNAL "All compiled and system-related runnable executables" )
  else()
    set( VIAME_EXECUTABLES_PATH
      ${VIAME_BUILD_INSTALL_PREFIX}/bin:$ENV{PATH}
      CACHE INTERNAL "All compiled and system-related runnable executables" )
  endif()
endif()

if( VIAME_ENABLE_CUDNN AND NOT VIAME_ENABLE_CUDA )
  message( FATAL_ERROR "Cannot enable CUDNN without CUDA, disable VIAME_ENABLE_CUDNN" )
endif()

if( VIAME_ENABLE_CUDNN )
  set( CUDNN_ROOT_DIR "" CACHE PATH "CUDNN root folder, leave as blank to auto-detect." )

  find_library( CUDNN_LIBRARY REQUIRED
    NAMES cudnn libcudnn.so libcudnn.so.8 libcudnn.so.7 libcudnn.so.6
    HINTS ${CUDNN_ROOT_DIR}
          ${CUDNN_ROOT_DIR}/lib
          ${CUDNN_ROOT_DIR}/lib/x64
          ${CUDA_TOOLKIT_ROOT_DIR}
          ${CUDA_TOOLKIT_ROOT_DIR}/lib
          ${CUDA_TOOLKIT_ROOT_DIR}/lib/x64
          ${CUDA_TOOLKIT_ROOT_DIR}/lib64
          ${CUDA_TOOLKIT_ROOT_DIR}/targets/aarch64-linux
    PATH_SUFFIXES lib lib64 )

  get_filename_component( CUDNN_LIBRARY "${CUDNN_LIBRARY}" REALPATH )

  if( NOT CUDNN_LIBRARY )
    message( FATAL_ERROR "Unable to locate CUDNN library" )
  endif()

  # Different subprojects use each variable
  set( CUDNN_LIBRARIES "${CUDNN_LIBRARY}" CACHE INTERNAL "" FORCE )

  # Check version of CUDNN
  get_filename_component( CUDNN_ROOT_DIR_TMP "${CUDNN_LIBRARY}" DIRECTORY )
  get_filename_component( CUDNN_ROOT_DIR_TMP "${CUDNN_ROOT_DIR_TMP}" DIRECTORY )

  set( CUDNN_ROOT_DIR "${CUDNN_ROOT_DIR_TMP}" CACHE INTERNAL "CUDNN root folder" FORCE )
  set( CUDNN_INCLUDE_FILE "${CUDNN_ROOT_DIR}/include/cudnn.h" CACHE INTERNAL "" FORCE )

  if( CUDNN_ROOT_DIR STREQUAL "/" )
    set( CUDNN_INCLUDE_FILE "/include/cudnn.h" CACHE INTERNAL "" FORCE )
  endif()

  if( NOT EXISTS ${CUDNN_INCLUDE_FILE} )
    get_filename_component( CUDNN_ROOT_DIR_TMP "${CUDNN_ROOT_DIR_TMP}" DIRECTORY )

    set( CUDNN_ROOT_DIR "${CUDNN_ROOT_DIR_TMP}" CACHE INTERNAL "CUDNN root folder" FORCE )
    set( CUDNN_INCLUDE_FILE "${CUDNN_ROOT_DIR}/include/cudnn.h" CACHE INTERNAL "" FORCE )
  endif()

  if( NOT EXISTS ${CUDNN_INCLUDE_FILE} )
    message( ERROR "Unable to locate cudnn.h include header" )
  endif()

  if( CUDNN_ROOT_DIR STREQUAL "/" )
    set( CUDNN_INCLUDE_DIR "/include" CACHE INTERNAL "CUDNN include" FORCE )
  else()
    set( CUDNN_INCLUDE_DIR "${CUDNN_ROOT_DIR}/include" CACHE INTERNAL "" FORCE )
  endif()

  if( EXISTS "${CUDNN_ROOT_DIR}/include/cudnn_version.h" )
    set( CUDNN_VERSION_FILE "${CUDNN_ROOT_DIR}/include/cudnn_version.h" )
  else()
    set( CUDNN_VERSION_FILE "${CUDNN_INCLUDE_FILE}" )
  endif()

  if( EXISTS "${CUDNN_VERSION_FILE}" )
    file( READ "${CUDNN_VERSION_FILE}" TMP_CUDNN_VERSION_FILE_CONTENTS )

    string( REGEX MATCH "define CUDNN_MAJOR * +([0-9]+)"
            CUDNN_VERSION_MAJOR "${TMP_CUDNN_VERSION_FILE_CONTENTS}" )
    string( REGEX REPLACE "define CUDNN_MAJOR * +([0-9]+)" "\\1"
            CUDNN_VERSION_MAJOR "${CUDNN_VERSION_MAJOR}" )
  endif()
endif()

if( VIAME_ENABLE_PYTHON )
  if( NOT WIN32 )
    option( VIAME_SYMLINK_PYTHON "Symlink python files instead of copying." OFF )
    mark_as_advanced( VIAME_SYMLINK_PYTHON )
  endif()
  set( KWIVER_SYMLINK_PYTHON ${VIAME_SYMLINK_PYTHON} ) # Required for KWIVER scripts

  if( VIAME_ENABLE_PYTHON-INTERNAL )
    include( setup_internal_python )
  else()
    find_package( Python COMPONENTS Interpreter Development REQUIRED )
  endif()

  # Backwards compatibility for sub-projects which use "PYTHON_" cmake
  # variables and the old find_package( PythonInterp ) commands instead
  # of the newer find Python. Copies all Python_* to PYTHON_* vars.
  CopyVarsToAllCaps( "Python" )

  if( VIAME_ENABLE_PYTHON-NETHARN AND NOT VIAME_ENABLE_PYTHON-MMDET )
    message( FATAL_ERROR "Netharn currently also requires mmdet enabled" )
  endif()

  set( VIAME_PYTHON_STRING "python${Python_VERSION_MAJOR}.${Python_VERSION_MINOR}"
    CACHE INTERNAL "Version ID used in python install paths" )

  set( PYBASE ${VIAME_BUILD_INSTALL_PREFIX}/lib/${VIAME_PYTHON_STRING} )
  set( VIAME_PYTHON_INSTALL ${PYBASE} CACHE INTERNAL "VIAME Python install path" )
  set( VIAME_PYTHON_USERBASE "${VIAME_INSTALL_PREFIX}" )

  # Add PYTHON_PATH variables internal to the VIAME build tree, e.g. things installed
  # just for VIAME not in an external Python environment or install
  set( PYTHON_PATH_DESC "Pythonpath for all files installed as a part of VIAME" )
  if( WIN32 )
    string( REPLACE "/" "\\" VIAME_PYTHON_USERBASE "${VIAME_PYTHON_USERBASE}" )
    set( VIAME_PYTHON_PATH
      ${PYBASE};${PYBASE}/site-packages;${PYBASE}/dist-packages
      CACHE INTERNAL ${PYTHON_PATH_DESC} )
    if( NOT VIAME_ENABLE_PYTHON-INTERNAL )
      # If using system python on windows, add all possible path locations for
      # python packages in the system install just so they can be used in addition
      # to the ones within the VIAME install tree
      if( EXISTS "${PYTHON_STDLIB}" AND EXISTS "${PYTHON_SITELIB}" )
        set( VIAME_PYTHON_PATH
          ${VIAME_PYTHON_PATH};${PYTHON_STDLIB};${PYTHON_SITELIB}
          CACHE INTERNAL ${PYTHON_PATH_DESC} )
       endif()
      if( EXISTS "${PYTHON_RUNTIME_LIBRARY_DIRS}/DLLs" )
        set( VIAME_PYTHON_PATH
          ${VIAME_PYTHON_PATH};${PYTHON_RUNTIME_LIBRARY_DIRS}/DLLs
          CACHE INTERNAL ${PYTHON_PATH_DESC} )
      endif()
    endif()
  else()
    set( VIAME_PYTHON_PATH
      ${PYBASE}:${PYBASE}/site-packages:${PYBASE}/dist-packages
      CACHE INTERNAL ${PYTHON_PATH_DESC} )
  endif()

  # Configure PYTHON_DEP_ENV_VARS, this is used to set the environment used for
  # either building or installing python dependencies
  set( PYTHON_DEP_ENV_VARS )

  if( WIN32 )
    set( ADJ_INCLUDE_PATH "${VIAME_INSTALL_PREFIX}/include;$ENV{INCLUDE}" )
    set( ADJ_LIBRARY_PATH "${VIAME_INSTALL_PREFIX}/lib;${VIAME_INSTALL_PREFIX}/bin;$ENV{LIB}" )

    if( VIAME_ENABLE_PYTHON-INTERNAL )
      set( ENV{PYTHONPATH} "${VIAME_PYTHON_PATH};$ENV{PYTHONPATH}" )
      list( APPEND PYTHON_DEP_ENV_VARS "PYTHONHOME=${VIAME_PYTHON_USERBASE}" )
    else()
      if( EXISTS "${PYTHON_INCLUDE_DIRS}" )
        set( ADJ_INCLUDE_PATH "${ADJ_INCLUDE_PATH};${PYTHON_INCLUDE_DIRS}" )
      endif()
      if( EXISTS "${PYTHON_LIBRARY_DIRS}" )
        set( ADJ_LIBRARY_PATH "${ADJ_LIBRARY_PATH};${PYTHON_LIBRARY_DIRS}" )
      endif()
    endif()

    string( REPLACE ";" "----" VIAME_PYTHON_PATH "${VIAME_PYTHON_PATH}" )
    string( REPLACE ";" "----" VIAME_EXECUTABLES_PATH "${VIAME_EXECUTABLES_PATH}" )
    string( REPLACE ";" "----" ADJ_INCLUDE_PATH "${ADJ_INCLUDE_PATH}" )
    string( REPLACE ";" "----" ADJ_LIBRARY_PATH "${ADJ_LIBRARY_PATH}" )

    list( APPEND PYTHON_DEP_ENV_VARS "INCLUDE=${ADJ_INCLUDE_PATH}" )
    list( APPEND PYTHON_DEP_ENV_VARS "LIB=${ADJ_LIBRARY_PATH}" )
    list( APPEND PYTHON_DEP_ENV_VARS "PYTHONIOENCODING=UTF-8" )
  else()
    set( ADJ_LD_LIB_PATH "${VIAME_INSTALL_PREFIX}/lib:$ENV{LD_LIBRARY_PATH}" )

    list( APPEND PYTHON_DEP_ENV_VARS "PATH=${VIAME_EXECUTABLES_PATH}" )
    list( APPEND PYTHON_DEP_ENV_VARS "CPPFLAGS=-I${VIAME_INSTALL_PREFIX}/include" )
    list( APPEND PYTHON_DEP_ENV_VARS "LDFLAGS=-L${VIAME_INSTALL_PREFIX}/lib" )
    list( APPEND PYTHON_DEP_ENV_VARS "CC=${CMAKE_C_COMPILER}" )
    list( APPEND PYTHON_DEP_ENV_VARS "CXX=${CMAKE_CXX_COMPILER}" )
    list( APPEND PYTHON_DEP_ENV_VARS "LD_LIBRARY_PATH=${ADJ_LD_LIB_PATH}" )
  endif()

  list( APPEND PYTHON_DEP_ENV_VARS "PYTHONPATH=${VIAME_PYTHON_PATH}" )
  list( APPEND PYTHON_DEP_ENV_VARS "PYTHONUSERBASE=${VIAME_PYTHON_USERBASE}" )
  list( APPEND PYTHON_DEP_ENV_VARS "PKG_CONFIG_PATH=${VIAME_INSTALL_PREFIX}/lib/pkgconfig" )
endif()

if( WIN32 AND VIAME_ENABLE_PYTHON AND CMAKE_CONFIGURATION_TYPES EQUAL "Debug" )
  message( FATAL_ERROR "Cannot build in Debug on Windows with Python enabled, \
    build in RelWithDebInfo or Release until fixed." )
endif()

# VXL enabled triggers yasm to be built, requiring at least some python
if( VIAME_ENABLE_VXL AND NOT VIAME_ENABLE_PYTHON-INTERNAL )
  if( NOT Python_FOUND AND NOT VIAME_ENABLE_PYTHON-INTERNAL )
    message( FATAL_ERROR "If VXL is enabled, there must be some python install \
      located on the system to build, even if VIAME_ENABLE_PYTHON is turned off \
      for all other packages. A python binary could not be found. Please install \
      at least python." )
  endif()
endif()

if( VIAME_ENABLE_PYTORCH )
  if( VIAME_ENABLE_PYTORCH-INTERNAL AND
      NOT VIAME_PYTORCH_VERSION VERSION_EQUAL "${PYTORCH_INTERNAL_VERSION}" )
    message( FATAL_ERROR "Only PyTorch ${PYTORCH_INTERNAL_VERSION} support with "
      "VIAME_ENABLE_PYTORCH-INTERNAL flag set. Either change VIAME_PYTORCH_VERSION "
      "to ${PYTORCH_INTERNAL_VERSION} or disable the flag VIAME_ENABLE_PYTORCH-INTERNAL." )
  endif()
  if( VIAME_ENABLE_CUDA )
    if( VIAME_PYTORCH_VERSION VERSION_EQUAL "1.13.1" AND
        NOT VIAME_ENABLE_PYTORCH-INTERNAL AND
        NOT ( CUDA_VERSION VERSION_EQUAL "11.6" OR
              CUDA_VERSION VERSION_EQUAL "11.7" ) )
      message( FATAL_ERROR "CUDA 11.7, or 11.6 is required for VIAME_ENABLE_PYTORCH "
        "with VIAME_ENABLE_PYTORCH-INTERNAL off and using PyTorch 1.13.1. Either modify "
        "VIAME_PYTORCH_VERSION, modify CUDA version, or enable internal pytorch build." )
    elseif( VIAME_PYTORCH_VERSION VERSION_EQUAL "1.11.0" AND
        NOT VIAME_ENABLE_PYTORCH-INTERNAL AND
        NOT ( CUDA_VERSION VERSION_EQUAL "10.2" OR
              CUDA_VERSION VERSION_EQUAL "11.3" OR
              CUDA_VERSION VERSION_EQUAL "11.5" ) )
      message( FATAL_ERROR "CUDA 11.5, 11.3 or 10.2 is required for VIAME_ENABLE_PYTORCH "
        "with VIAME_ENABLE_PYTORCH-INTERNAL off and using PyTorch 1.11.0. Either modify "
        "VIAME_PYTORCH_VERSION, modify CUDA version, or enable internal pytorch build." )
    elseif( VIAME_PYTORCH_VERSION VERSION_EQUAL "1.10.2" AND
            NOT VIAME_ENABLE_PYTORCH-INTERNAL AND
            NOT ( CUDA_VERSION VERSION_EQUAL "10.2" OR
                  CUDA_VERSION VERSION_EQUAL "11.1" OR
                  CUDA_VERSION VERSION_EQUAL "11.3" ) )
      message( FATAL_ERROR "CUDA 11.3, 11.1 or 10.2 is required for VIAME_ENABLE_PYTORCH "
        "with VIAME_ENABLE_PYTORCH-INTERNAL off and using PyTorch 1.10.2. Either modify "
        "VIAME_PYTORCH_VERSION, modify CUDA version, or enable internal pytorch build." )
    elseif( CUDA_VERSION VERSION_LESS "11.0" AND
            VIAME_ENABLE_PYTORCH-INTERNAL )
      message( FATAL_ERROR "A CUDA version > 11.0 is required for an internal build "
        "of pytorch. Either disable VIAME_ENABLE_PYTORCH-INTERNAL or downgrade CUDA." )
    elseif( CUDA_VERSION VERSION_LESS "10.1" )
      message( FATAL_ERROR "At least CUDA 10.1 required for VIAME_ENABLE_PYTORCH. "
        "Upgrading your CUDA version is recommended." )
    elseif( VIAME_ENABLE_PYTORCH-VIS-INTERNAL AND
            CUDA_VERSION VERSION_LESS "11.0" )
      message( FATAL_ERROR "VIAME_ENABLE_PYTORCH-VIS-INTERNAL requires at least CUDA 11.0" )
    elseif( VIAME_ENABLE_PYTORCH-INTERNAL AND
            VIAME_ENABLE_CUDNN AND
            CUDNN_VERSION_MAJOR VERSION_LESS "7.0.0" )
      message( FATAL_ERROR "CUDNN 7.0 or higher required for internal pytorch build" )
    elseif( Python_VERSION VERSION_LESS "3.7.0" AND
            VIAME_PYTORCH_VERSION VERSION_GREATER_EQUAL "1.11.0" )
      message( FATAL_ERROR "At least Python 3.7 is required for PyTorch versions "
        "greater than 1.11.0, either upgrade python or set VIAME_PYTORCH_VERSION "
        "to be 1.10.2. If you think you have Python3.7+ installed, make sure you "
        "also have the python header package installed, e.g. python3-dev." )
    elseif( VIAME_BUILD_CHECKS AND Python_VERSION VERSION_LESS "3.6.2" )
      message( FATAL_ERROR "Only python distributions  >= 3.6.2 are currently "
        "supported with pytorch enabled. Disable VIAME_BUILD_CHECKS to "
        "attempt to use your current version. If you think you have Python3.6+ "
        "installed, make sure you also have the python header package installed, "
        "e.g. python3-dev or python3-devel." )
    endif()
  endif()
endif()

if( VIAME_ENABLE_OPENCV )
  set( VIAME_OPENCV_VERSION 4.2.0 CACHE STRING "Version of OpenCV to use" )
  set_property( CACHE VIAME_OPENCV_VERSION PROPERTY STRINGS "3.4.0" "4.2.0" "4.5.1" )
  mark_as_advanced( VIAME_OPENCV_VERSION )

  if( CMAKE_COMPILER_IS_GNUCC AND
      CMAKE_CXX_COMPILER_VERSION VERSION_GREATER 12.0 AND
      VIAME_OPENCV_VERSION VERSION_LESS "4.5" )
    message( FATAL_ERROR "GCC compiler version 12 is very new. For compatibility "
      "reasons, VIAME_OPENCV_VERSION should be set to 4.5.1 or greater."  )
  endif()
endif()

if( VIAME_ENABLE_DIVE AND NOT VIAME_ENABLE_FFMPEG-X264 )
  message( FATAL_ERROR "VIAME_ENABLE_DIVE requires VIAME_ENABLE_FFMPEG-X264 flag" )
endif()

# Set default windows configuration mode to be 'Release'
set( VIAME_FIRST_CONFIGURATION TRUE CACHE BOOL "Has this project been configured." )
mark_as_advanced( VIAME_FIRST_CONFIGURATION )

if( MSVC AND VIAME_FIRST_CONFIGURATION )
  set( CMAKE_CONFIGURATION_TYPES "Release" CACHE STRING "This specifies what \
    build types (configurations) will be available for selection within \
	  Visual Studio. Options are: Release, RelWithDebInfo, Debug etc. in a \
	  semi-colon seperated list." FORCE )

  set( VIAME_FIRST_CONFIGURATION FALSE CACHE BOOL "Project has been configured." FORCE )
endif()

if( MSVC AND CMAKE_CXX_COMPILER_VERSION VERSION_LESS "18.00" )
  message( FATAL_ERROR "You must use at least MSVC version 13 or greater" )
endif()
# if we have a 32 bit build, turn off Eigen alignment for more information see:
# http://eigen.tuxfamily.org/dox/group__TopicUnalignedArrayAssert.html
if( CMAKE_SIZEOF_VOID_P EQUAL 4 )
  set(CMAKE_CXX_FLAGS
    "${CMAKE_CXX_FLAGS} -DEIGEN_DONT_VECTORIZE -DEIGEN_DISABLE_UNALIGNED_ARRAY_ASSERT")
endif()

###
# Main build loop for when we are building both VIAME and all dependencies
##
if( VIAME_BUILD_DEPENDENCIES )

  # Early error checking in case user did not run submodule init
  file( GLOB fletch_files ${VIAME_PACKAGES_DIR}/fletch/* )
  list( LENGTH fletch_files fletch_length )

  if( ${fletch_length} LESS 3 )
    message( FATAL_ERROR "Fletch directory empty, did you not run the following in \
     your source tree: \n git submodule update --init --recursive" )
  endif()

  # Include for CMake external project add command
  include( ExternalProject )

  # Specifies internal arguments passed to all projects (CXX flag passdowns, etc)
  include( common_args )

  # Core dependencies for other projects
  include( add_project_fletch )

  if( VIAME_ENABLE_PYTHON )
    include( add_project_python_deps )
  endif()

  # Add optional projects dependend on by other projects
  if( VIAME_ENABLE_DARKNET )
    include( add_project_darknet )
  endif()

  if( VIAME_ENABLE_BURNOUT )
    include( add_project_burnout )
  endif()

  if( VIAME_ENABLE_SMQTK )
    include( add_project_smqtk )
  endif()

  # Add (usually required) kwiver requirement
  if( VIAME_ENABLE_KWIVER )
    include( add_project_kwiver )
  endif()

  # Add other optional libraries
  if( VIAME_ENABLE_POSTGRESQL )
    include( add_project_postgres )
  endif()

  if( VIAME_ENABLE_SCALLOP_TK )
    include( add_project_scallop_tk )
  endif()

  if( VIAME_ENABLE_VIVIA )
    include( add_project_vivia )
  endif()

  if( VIAME_ENABLE_SEAL )
    include( add_project_seal_tk )
  endif()

  if( VIAME_ENABLE_DIVE )
    include( add_project_dive )
  endif()

  if( VIAME_ENABLE_KWANT )
    include( add_project_kwant )
  endif()

  if( VIAME_ENABLE_TENSORRT )
    include( add_project_tensorrt )
  endif()

  if( VIAME_ENABLE_PYTORCH )
    include( add_project_pytorch )
  endif()

  if( VIAME_ENABLE_LEARN )
    include( add_project_learn )
  endif()

  if( VIAME_ENABLE_TENSORFLOW )
    include( add_project_tensorflow )
  endif()

  if( VIAME_ENABLE_ITK )
    include( add_project_itk_extras )
  endif()

  if( VIAME_ENABLE_KEYPOINTGUI )
    include( add_project_keypointgui )
  endif()

  # VIAME plugins, adds this project causing the below else() block to run
  if( VIAME_ENABLE_VIAME_PLUGINS )
    include( add_project_viame )
  endif()

  # Fixup installer package
  if( VIAME_FIXUP_BUNDLE )
    include( build_package )
  endif()
else()

  include_directories( "${CMAKE_CURRENT_BINARY_DIR}" )

  ###
  # Look for and use Fletch to find dependencies
  ##
  if( IS_DIRECTORY ${fletch_DIR} )
    find_package( fletch NO_MODULE )
    list( APPEND CMAKE_PREFIX_PATH  "${fletch_DIR}" )
  endif()

  ###
  # Require OpenCV if enabled
  ##
  if( VIAME_ENABLE_OPENCV )
    find_package( OpenCV REQUIRED )
  endif()

  ###
  # KWIVER configuration variables
  ##
  if( VIAME_ENABLE_KWIVER )
    find_package( kwiver REQUIRED )

    include_directories( ${KWIVER_INCLUDE_DIRS} )
    link_directories( ${KWIVER_LIBRARY_DIR} )
    list( INSERT CMAKE_MODULE_PATH 0 "${KWIVER_CMAKE_DIR}" )
    include_directories( "${KWIVER_INCLUDE_DIRS}" )

    # Setup python directories before call to import kwiver utils
    #
    # This will trigger use of our desired python output paths on latest
    if( VIAME_ENABLE_PYTHON )
      set( KWIVER_BINARY_DIR "${VIAME_BINARY_DIR}" )

      set( kwiver_python_subdir "${VIAME_PYTHON_STRING}" )
      set( kwiver_python_output_path "${VIAME_BUILD_PREFIX}/${kwiver_python_subdir}" )
      set( kwiver_python_install_path "${VIAME_BUILD_INSTALL_PREFIX}/lib/${kwiver_python_subdir}" )

      set( viame_python_install_path "${kwiver_python_install_path}" )
    endif()

    include( kwiver-cmake-future )
    include( kwiver-utils )

    ###
    # System specific compiler flags
    ##
    include( viame-flags )

    ##
    # check compiler support
    include( kwiver-configcheck )

    # set the name for our package exports and plugin directories
    set( kwiver_export_name                           viame_exports )

    set( kwiver_plugin_subdir                         viame )
    set( kwiver_plugin_process_subdir                 ${kwiver_plugin_subdir}/processes )
    set( kwiver_plugin_process_instrumentation_subdir ${kwiver_plugin_subdir}/modules )
    set( kwiver_plugin_algorithm_subdir               ${kwiver_plugin_subdir}/modules )
    set( kwiver_plugin_scheduler_subdir               ${kwiver_plugin_subdir}/processes )
    set( kwiver_plugin_module_subdir                  ${kwiver_plugin_subdir}/modules )
    set( kwiver_plugin_plugin_explorer_subdir         ${kwiver_plugin_subdir}/modules/plugin_explorer )
    set( kwiver_plugin_logger_subdir                  ${kwiver_plugin_subdir}/modules )

    ##
    # Build system hacks which should eventually be fixed better
    include( windows-ksys-hack )
    include( linux-remove-duplicate-cvs )
  endif()

  ###
  # Add VIAME subdirs
  ##
  if( VIAME_ENABLE_KWIVER )
    add_subdirectory( plugins )
  endif()

  add_subdirectory( examples )
  add_subdirectory( configs )
  add_subdirectory( tools )

  ###
  # Configure setup scripts
  ##
  include( setup_viame_paths )

  if( WIN32 )
    set( VIAME_SETUP_SCRIPT "${VIAME_BINARY_DIR}/setup_viame.bat" )

    if( VIAME_FIXUP_BUNDLE OR VIAME_VERSION_RELEASE )
      configure_file(
        ${VIAME_CMAKE_DIR}/setup_viame.rel.bat.in
        ${VIAME_SETUP_SCRIPT}
        @ONLY
      )
    else()
      configure_file(
        ${VIAME_CMAKE_DIR}/setup_viame.dev.bat.in
        ${VIAME_SETUP_SCRIPT}
        @ONLY
      )
    endif()

    install( PROGRAMS      ${VIAME_SETUP_SCRIPT}
             DESTINATION   ${CMAKE_INSTALL_PREFIX} )

    if( VIAME_ENABLE_SEAL )
      install( PROGRAMS     "${VIAME_CMAKE_DIR}/launch_seal_interface.bat"
               DESTINATION   ${CMAKE_INSTALL_PREFIX} )
    endif()
    if( VIAME_ENABLE_DIVE )
      install( PROGRAMS     "${VIAME_CMAKE_DIR}/launch_dive_interface.bat"
               DESTINATION   ${CMAKE_INSTALL_PREFIX} )
    endif()
  else()
    set( VIAME_SETUP_SCRIPT_FILE    "${VIAME_BINARY_DIR}/setup_viame.sh" )

    if( VIAME_FIXUP_BUNDLE OR VIAME_VERSION_RELEASE )
      configure_file(
        ${VIAME_CMAKE_DIR}/setup_viame.rel.sh.in
        ${VIAME_SETUP_SCRIPT_FILE}
        @ONLY
      )
    else()
      configure_file(
        ${VIAME_CMAKE_DIR}/setup_viame.dev.sh.in
        ${VIAME_SETUP_SCRIPT_FILE}
        @ONLY
      )
    endif()

    install( PROGRAMS      ${VIAME_SETUP_SCRIPT_FILE}
             DESTINATION   ${CMAKE_INSTALL_PREFIX} )
    install( PROGRAMS      ${VIAME_CMAKE_DIR}/download_viame_addons.sh
             DESTINATION   ${CMAKE_INSTALL_PREFIX}/bin )
    install( PROGRAMS      ${VIAME_CMAKE_DIR}/download_viame_addons.csv
             DESTINATION   ${CMAKE_INSTALL_PREFIX}/bin )
    install( PROGRAMS      ${VIAME_CMAKE_DIR}/filter_non_web_pipelines.sh
             DESTINATION   ${CMAKE_INSTALL_PREFIX}/bin )
    install( PROGRAMS      ${VIAME_CMAKE_DIR}/limit_train_time_for_viame_web.sh
             DESTINATION   ${CMAKE_INSTALL_PREFIX}/bin )

    if( VIAME_ENABLE_SEAL )
      install( PROGRAMS      "${VIAME_CMAKE_DIR}/launch_seal_interface.sh"
               DESTINATION   ${CMAKE_INSTALL_PREFIX} )
    endif()
    if( VIAME_ENABLE_DIVE )
      install( PROGRAMS      "${VIAME_CMAKE_DIR}/launch_dive_interface.sh"
               DESTINATION   ${CMAKE_INSTALL_PREFIX} )
    endif()
  endif()

  ###
  # Install system libs if packaging enabled
  ##
  if( VIAME_FIXUP_BUNDLE )
    set( VIAME_RELEASE_NOTES_FILE "RELEASE_NOTES.md" )

    install( PROGRAMS      ${VIAME_RELEASE_NOTES_FILE}
             DESTINATION   ${CMAKE_INSTALL_PREFIX} )

    set( CMAKE_INSTALL_UCRT_LIBRARIES TRUE )
    include( InstallRequiredSystemLibraries )
    if( CMAKE_INSTALL_SYSTEM_RUNTIME_LIBS )
      install( PROGRAMS ${CMAKE_INSTALL_SYSTEM_RUNTIME_LIBS} DESTINATION bin COMPONENT System )
    endif()

    if( VIAME_ENABLE_CUDNN )
      install( FILES ${CUDNN_LIBRARY} DESTINATION lib )
    endif()

    configure_file(
      ${VIAME_CMAKE_DIR}/viame-install-fixup.cmake.in
      ${CMAKE_BINARY_DIR}/viame-install-fixup.cmake
      @ONLY
      )
    install( SCRIPT ${CMAKE_BINARY_DIR}/viame-install-fixup.cmake )
  endif()
endif()
