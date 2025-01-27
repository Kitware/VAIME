# PyTorch External Project
#
# Required symbols are:
#   VIAME_BUILD_PREFIX - where packages are built
#   VIAME_INSTALL_PREFIX - directory install target
#   VIAME_PACKAGES_DIR - location of git submodule packages
#   VIAME_ARGS_COMMON -
##

CreateDirectory( ${VIAME_BUILD_PREFIX}/src/pytorch-build )

set( PYTORCH_LIBS_TO_BUILD )

if( VIAME_PYTORCH_BUILD_FROM_SOURCE )
  set( PYTORCH_LIBS_TO_BUILD ${PYTORCH_LIBS_TO_BUILD} pytorch )
endif()

if( VIAME_PYTORCH_BUILD_TORCHVISION )
  set( PYTORCH_LIBS_TO_BUILD ${PYTORCH_LIBS_TO_BUILD} torchvision )
endif()

if( VIAME_ENABLE_PYTORCH-VIDEO )
  set( PYTORCH_LIBS_TO_BUILD ${PYTORCH_LIBS_TO_BUILD} pyav torchvideo )
endif()

if( VIAME_ENABLE_PYTORCH-MMDET OR VIAME_ENABLE_PYTORCH-NETHARN )
  set( PYTORCH_LIBS_TO_BUILD ${PYTORCH_LIBS_TO_BUILD} imgaug )
endif()

if( VIAME_ENABLE_PYTORCH-MMDET )
  set( PYTORCH_LIBS_TO_BUILD ${PYTORCH_LIBS_TO_BUILD} mmcv mmdetection )
endif()

if( VIAME_ENABLE_ONNX AND VIAME_ENABLE_DARKNET)
  set( PYTORCH_LIBS_TO_BUILD ${PYTORCH_LIBS_TO_BUILD} darknet-to-pytorch-onnx )
endif()

if( VIAME_ENABLE_ONNX AND VIAME_ENABLE_PYTORCH-MMDET )
  set( PYTORCH_LIBS_TO_BUILD ${PYTORCH_LIBS_TO_BUILD} mmdeploy )
endif()

if( VIAME_ENABLE_PYTORCH-PYSOT )
  set( PYTORCH_LIBS_TO_BUILD ${PYTORCH_LIBS_TO_BUILD} pysot )
endif()

if( VIAME_ENABLE_PYTORCH-MDNET )
  set( PYTORCH_LIBS_TO_BUILD ${PYTORCH_LIBS_TO_BUILD} roi-align )
endif()

if( VIAME_ENABLE_PYTORCH-NETHARN )
  set( PYTORCH_LIBS_TO_BUILD ${PYTORCH_LIBS_TO_BUILD} netharn bioharn )
endif()

if( VIAME_ENABLE_PYTORCH-DETECTRON )
  set( PYTORCH_LIBS_TO_BUILD ${PYTORCH_LIBS_TO_BUILD} detectron2 )
endif()

if( VIAME_ENABLE_PYTORCH-SAM )
  set( PYTORCH_LIBS_TO_BUILD ${PYTORCH_LIBS_TO_BUILD} sam2 )
endif()

if( VIAME_ENABLE_TENSORRT )
  set( PYTORCH_LIBS_TO_BUILD ${PYTORCH_LIBS_TO_BUILD} torch2rt )
endif()

set( VIAME_PROJECT_LIST ${VIAME_PROJECT_LIST} ${PYTORCH_LIBS_TO_BUILD} )
set( PYTORCH_ENV_VARS ${PYTHON_DEP_ENV_VARS} )

if( VIAME_ENABLE_CUDNN )
  if( WIN32 )
    string( REPLACE ";" "----" CUDNN_ADJ_LIB_LIST "${CUDNN_LIBRARIES}" )
    list( APPEND PYTORCH_ENV_VARS "CUDNN_LIBRARY=${CUDNN_ADJ_LIB_LIST}" )
  else()
    list( APPEND PYTORCH_ENV_VARS "CUDNN_LIBRARY=${CUDNN_LIBRARIES}" )
  endif()
  if( CUDNN_ROOT_DIR )
    list( APPEND PYTORCH_ENV_VARS "CUDNN_INCLUDE_DIR=${CUDNN_ROOT_DIR}/include" )
  endif()
endif()

if( VIAME_PYTORCH_DISABLE_NINJA )
  list( APPEND PYTORCH_ENV_VARS "USE_NINJA=OFF" )
endif()

if( VIAME_ENABLE_PYTORCH-NETHARN )
  list( APPEND PYTORCH_ENV_VARS "BEZIER_NO_EXTENSION=1" )
endif()

if( VIAME_ENABLE_CUDA )
  list( APPEND PYTORCH_ENV_VARS "USE_CUDA=1" )
  list( APPEND PYTORCH_ENV_VARS "FORCE_CUDA=1" )
  list( APPEND PYTORCH_ENV_VARS "CUDA_VISIBLE_DEVICES=0" )
  list( APPEND PYTORCH_ENV_VARS "CUDA_HOME=${CUDA_TOOLKIT_ROOT_DIR}" )
  list( APPEND PYTORCH_ENV_VARS "TORCH_CUDA_ARCH_LIST=${CUDA_ARCHITECTURES}" )
  list( APPEND PYTORCH_ENV_VARS "TORCH_NVCC_FLAGS=-Xfatbin -compress-all" )
  list( APPEND PYTORCH_ENV_VARS "NO_CAFFE2_OPS=1" )
else()
  list( APPEND PYTORCH_ENV_VARS "USE_CUDA=0" )
endif()

if( VIAME_ENABLE_PYTORCH-MMDET )
  list( APPEND PYTORCH_ENV_VARS "MMCV_WITH_OPS=1" )
endif()

if( VIAME_PYTORCH_BUILD_TORCHVISION AND NOT WIN32 )
  list( APPEND PYTORCH_ENV_VARS "TORCHVISION_USE_PNG=0" )
endif()

if( WIN32 AND VIAME_ENABLE_LEARN AND Python_VERSION VERSION_GREATER "3.7" )
  list( APPEND PYTORCH_ENV_VARS "SETUPTOOLS_USE_DISTUTILS=1" )
endif()

foreach( LIB ${PYTORCH_LIBS_TO_BUILD} )
  if( "${LIB}" STREQUAL "pytorch" )
    set( LIBRARY_LOCATION ${VIAME_PACKAGES_DIR}/pytorch )
  elseif( "${LIB}" STREQUAL "roi-align" )
    set( LIBRARY_LOCATION ${VIAME_SOURCE_DIR}/plugins/pytorch/mdnet )
  elseif( "${LIB}" STREQUAL "pyav" )
    set( LIBRARY_LOCATION ${VIAME_PACKAGES_DIR}/python-utils/pyav )
  else()
    set( LIBRARY_LOCATION ${VIAME_PACKAGES_DIR}/pytorch-libs/${LIB} )
  endif()

  set( LIBRARY_LOCATION_URL file://${LIBRARY_LOCATION} )

  set( LIBRARY_PIP_CACHE_DIR ${VIAME_BUILD_PREFIX}/src/pytorch-build/${LIB}-cache )
  set( LIBRARY_PIP_BUILD_DIR ${VIAME_BUILD_PREFIX}/src/pytorch-build/${LIB}-build )
  set( LIBRARY_PIP_TMP_DIR ${VIAME_BUILD_PREFIX}/src/pytorch-build/${LIB}-tmp )

  CreateDirectory( ${LIBRARY_PIP_CACHE_DIR} )
  CreateDirectory( ${LIBRARY_PIP_BUILD_DIR} )
  CreateDirectory( ${LIBRARY_PIP_TMP_DIR} )

  set( LIBRARY_PIP_BUILD_DIR_CMD -b ${LIBRARY_PIP_BUILD_DIR} )
  set( LIBRARY_PIP_CACHE_DIR_CMD --cache-dir ${LIBRARY_PIP_CACHE_DIR} )

  if( VIAME_PYTHON_SYMLINK )
    set( LIBRARY_PIP_BUILD_CMD
      ${Python_EXECUTABLE} setup.py build )
    set( LIBRARY_PIP_INSTALL_CMD
      ${Python_EXECUTABLE} -m pip install --user -e . )
  else()
    if( "${LIB}" STREQUAL "mmcv" OR "${LIB}" STREQUAL "torchvision" )
      set( LIBRARY_PIP_BUILD_CMD
        ${Python_EXECUTABLE} setup.py
          bdist_wheel -d ${LIBRARY_PIP_BUILD_DIR} )
    else()
      set( LIBRARY_PIP_BUILD_CMD
        ${Python_EXECUTABLE} setup.py build_ext
          --include-dirs="${VIAME_INSTALL_PREFIX}/include"
          --library-dirs="${VIAME_INSTALL_PREFIX}/lib"
          --inplace bdist_wheel -d ${LIBRARY_PIP_BUILD_DIR} )
    endif()
    set( LIBRARY_PIP_INSTALL_CMD
      ${CMAKE_COMMAND}
        -DPYTHON_EXECUTABLE=${Python_EXECUTABLE}
        -DPython_EXECUTABLE=${Python_EXECUTABLE}
        -DWHEEL_DIR=${LIBRARY_PIP_BUILD_DIR}
        -P ${VIAME_CMAKE_DIR}/install_python_wheel.cmake )
  endif()

  set( LIBRARY_PYTHON_BUILD
    ${CMAKE_COMMAND} -E env "${PYTORCH_ENV_VARS}"
    "TMPDIR=${LIBRARY_PIP_TMP_DIR}"
    ${LIBRARY_PIP_BUILD_CMD} )
  set( LIBRARY_PYTHON_INSTALL
    ${CMAKE_COMMAND} -E env "${PYTORCH_ENV_VARS}"
    "TMPDIR=${LIBRARY_PIP_TMP_DIR}"
    ${LIBRARY_PIP_INSTALL_CMD} )

  set( LIBRARY_PATCH_COMMAND "" )

  if( "${LIB}" STREQUAL "bioharn" )
    set( PROJECT_DEPS netharn )
  elseif( "${LIB}" STREQUAL "netharn" )
    set( PROJECT_DEPS mmdetection )
  elseif( "${LIB}" STREQUAL "mmdetection" )
    set( PROJECT_DEPS fletch mmcv )
    if( VIAME_ENABLE_PYTORCH-VISION )
      set( PROJECT_DEPS ${PROJECT_DEPS} torchvision )
    endif()
  elseif( "${LIB}" STREQUAL "pytorch" )
    set( PROJECT_DEPS fletch python-deps )
    if( Python_VERSION VERSION_LESS "3.7" AND
        VIAME_PYTORCH_VERSION VERSION_GREATER_EQUAL 1.11.0 )
      set( LIBRARY_PATCH_COMMAND ${CMAKE_COMMAND} -E copy_directory
        ${VIAME_PATCHES_DIR}/pytorch
        ${VIAME_PACKAGES_DIR}/pytorch )
    endif()
  elseif( "${LIB}" STREQUAL "torch2rt" )
    set( PROJECT_DEPS fletch python-deps tensorrt )
  elseif( "${LIB}" STREQUAL "torchvision" )
    set( PROJECT_DEPS fletch python-deps pytorch )
    if( VIAME_PYTORCH_VERSION VERSION_LESS "1.11" OR
        Python_VERSION VERSION_LESS "3.7" )
      set( LIBRARY_PATCH_COMMAND ${CMAKE_COMMAND} -E copy_directory
        ${VIAME_PATCHES_DIR}/torchvision
        ${VIAME_PACKAGES_DIR}/pytorch-libs/torchvision )
    endif()
  elseif( "${LIB}" STREQUAL "detectron2" )
    set( PROJECT_DEPS fletch python-deps pytorch )
    if( VIAME_ENABLE_PYTORCH-NETHARN )
      set( PROJECT_DEPS ${PROJECT_DEPS} bioharn )
    endif()
    if( WIN32 )
      set( LIBRARY_PATCH_COMMAND ${CMAKE_COMMAND} -E copy_directory
        ${VIAME_PATCHES_DIR}/detectron2
        ${VIAME_PACKAGES_DIR}/pytorch-libs/detectron2 )
    endif()
  elseif( "${LIB}" STREQUAL "pyav" )
    set( PROJECT_DEPS fletch python-deps )
    set( LIBRARY_PATCH_COMMAND ${CMAKE_COMMAND} -E copy_directory
      ${VIAME_PATCHES_DIR}/pyav
      ${VIAME_PACKAGES_DIR}/python-utils/pyav )
  elseif( "${LIB}" STREQUAL "torchvideo" )
    set( PROJECT_DEPS fletch python-deps pytorch pyav )
    if( Python_VERSION VERSION_LESS "3.7" )
      set( LIBRARY_PATCH_COMMAND ${CMAKE_COMMAND} -E copy_directory
        ${VIAME_PATCHES_DIR}/torchvideo
        ${VIAME_PACKAGES_DIR}/pytorch-libs/torchvideo )
    endif()
  elseif( "${LIB}" STREQUAL "sam2" )
    if( Python_VERSION VERSION_LESS "3.10" )
      set( LIBRARY_PATCH_COMMAND ${CMAKE_COMMAND} -E copy_directory
        ${VIAME_PATCHES_DIR}/sam2
        ${VIAME_PACKAGES_DIR}/pytorch-libs/sam2 )
    endif()
  elseif( "${LIB}" STREQUAL "mmdeploy" )
    set( PROJECT_DEPS fletch python-deps pytorch mmdetection mmcv onnxruntimelibs )
  else()
    set( PROJECT_DEPS fletch python-deps pytorch )
  endif()

  if( VIAME_ENABLE_SMQTK )
    set( PROJECT_DEPS ${PROJECT_DEPS} smqtk )
  endif()

  if ("${LIB}" STREQUAL "mmdeploy")

    set( ONNXRUNTIME_DIR ${VIAME_PYTHON_PACKAGES}/onnxruntime/onnxruntimelibs )
    set( LIBRARY_CPP_BUILD_DIR ${VIAME_SOURCE_DIR}/packages/pytorch-libs/mmdeploy/build )
    file( MAKE_DIRECTORY ${LIBRARY_CPP_BUILD_DIR} )

    set( LIBRARY_CPP_CONFIG
      ${CMAKE_COMMAND}
      -DMMDEPLOY_TARGET_BACKENDS=ort
      -DONNXRUNTIME_DIR=${ONNXRUNTIME_DIR}
      -S "${LIBRARY_LOCATION}"
      -B "${LIBRARY_CPP_BUILD_DIR}" )

    set(LIBRARY_CPP_BUILD ${CMAKE_COMMAND} --build "${LIBRARY_CPP_BUILD_DIR}")
    set(LIBRARY_CPP_INSTALL ${CMAKE_COMMAND} --install "${LIBRARY_CPP_BUILD_DIR}")
    if ((CMAKE_CONFIGURATION_TYPES STREQUAL "Release") OR (CMAKE_BUILD_TYPE STREQUAL "Release"))
      list( APPEND LIBRARY_CPP_BUILD --config Release)
      list( APPEND LIBRARY_CPP_INSTALL --config Release)
    endif()

    ExternalProject_Add( ${LIB}
      DEPENDS ${PROJECT_DEPS}
      PREFIX ${VIAME_BUILD_PREFIX}
      SOURCE_DIR ${LIBRARY_LOCATION}
      BUILD_IN_SOURCE 1
      PATCH_COMMAND ${LIBRARY_PATCH_COMMAND}
      CONFIGURE_COMMAND ${LIBRARY_CPP_CONFIG}
      BUILD_COMMAND ${LIBRARY_CPP_BUILD} && ${LIBRARY_CPP_INSTALL} && ${LIBRARY_PYTHON_BUILD}
      INSTALL_COMMAND ${LIBRARY_PYTHON_INSTALL}
      LIST_SEPARATOR "----" )

    set( MMDEPLOY_INSTALL_DIR ${VIAME_PYTHON_INSTALL}/site-packages/mmdeploy)
    ExternalProject_Add_Step(${LIB}
      postinstall
      COMMAND ${CMAKE_COMMAND} -E copy_directory ${LIBRARY_LOCATION}/configs ${MMDEPLOY_INSTALL_DIR}/configs
      DEPENDEES install )

  else()
    ExternalProject_Add( ${LIB}
      DEPENDS ${PROJECT_DEPS}
      PREFIX ${VIAME_BUILD_PREFIX}
      SOURCE_DIR ${LIBRARY_LOCATION}
      BUILD_IN_SOURCE 1
      PATCH_COMMAND ${LIBRARY_PATCH_COMMAND}
      CONFIGURE_COMMAND ""
      BUILD_COMMAND ${LIBRARY_PYTHON_BUILD}
      INSTALL_COMMAND ${LIBRARY_PYTHON_INSTALL}
      LIST_SEPARATOR "----"
      )
  endif()

  if( VIAME_FORCEBUILD )
    ExternalProject_Add_Step( ${LIB} forcebuild
      COMMAND ${CMAKE_COMMAND}
        -E remove ${VIAME_BUILD_PREFIX}/src/{LIB}-stamp
      COMMENT "Removing build stamp file for build update (forcebuild)."
      DEPENDEES configure
      DEPENDERS build
      ALWAYS 1
      )
  endif()
endforeach()

set( VIAME_ARGS_pytorch
  -Dpytorch_DIR:PATH=${VIAME_BUILD_PREFIX}/src/pytorch-build
  )
