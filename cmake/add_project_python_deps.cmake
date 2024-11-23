# ------------------------------------------------------------------------------------------------
# Python Dependency External Project
#
# Required symbols are:
#   VIAME_BUILD_PREFIX - where packages are built
#   VIAME_INSTALL_PREFIX - directory install target
#   VIAME_PACKAGES_DIR - location of git submodule packages
#   VIAME_ARGS_COMMON -
##

# ------------------------------ ADD ANY BASIC PYTHON DEPS HERE ----------------------------------
# Basic dependencies are installed jointly in one local pip installation call

# Core requirements used for building certain libraries
set( VIAME_PYTHON_BASIC_DEPS "wheel" "ordered_set" "cython<3.0.0" )

if( VIAME_FIXUP_BUNDLE )
  list( APPEND VIAME_PYTHON_BASIC_DEPS "numpy==1.19.3" )
else()
  list( APPEND  VIAME_PYTHON_BASIC_DEPS "numpy<=1.23.5" )
endif()

if( VIAME_BUILD_TESTS )
  list( APPEND VIAME_PYTHON_BASIC_DEPS "pytest" )
endif()

# Setuptools < 58.0 required for current version of gdal on windows or earlier python
if( ( WIN32 OR Python_VERSION VERSION_LESS "3.8" )
    AND VIAME_ENABLE_PYTORCH-NETHARN
    AND VIAME_ENABLE_GDAL )
  list( APPEND VIAME_PYTHON_BASIC_DEPS "setuptools==57.5.0" )
endif()

# For scoring and plotting
list( APPEND VIAME_PYTHON_BASIC_DEPS "kiwisolver==1.2.0" )
list( APPEND VIAME_PYTHON_BASIC_DEPS "matplotlib<=3.5.1" )

# For netharn and mmdet de-pickle on older versions
if( Python_VERSION VERSION_LESS "3.8" )
  list( APPEND VIAME_PYTHON_BASIC_DEPS "pickle5" )

  if( VIAME_ENABLE_PYTORCH-PYSOT )
    list( APPEND VIAME_PYTHON_BASIC_DEPS "protobuf==3.19.4" )
  endif()
endif()

# For fusion classifier
list( APPEND VIAME_PYTHON_BASIC_DEPS "map_boxes" "ensemble_boxes" )

if( Python_VERSION VERSION_LESS "3.9" )
  list( APPEND VIAME_PYTHON_BASIC_DEPS  "llvmlite==0.31.0" "numba==0.47" )
else()
  list( APPEND VIAME_PYTHON_BASIC_DEPS  "llvmlite==0.40.0" "numba==0.57" )
endif()

# For pytorch building
if( VIAME_ENABLE_PYTORCH-INTERNAL )
  list( APPEND VIAME_PYTHON_BASIC_DEPS "typing-extensions" "bs4" )
endif()

# For mmdetection
if( VIAME_ENABLE_PYTORCH-MMDET )
  if( Python_VERSION VERSION_LESS "3.8" )
    list( APPEND VIAME_PYTHON_BASIC_DEPS "yapf<=0.32.0" )
  else()
    list( APPEND VIAME_PYTHON_BASIC_DEPS "yapf" )
  endif()
endif()

# For measurement scripts
if( VIAME_ENABLE_OPENCV )
  list( APPEND VIAME_PYTHON_BASIC_DEPS "tqdm" "scipy" )
endif()

if( VIAME_ENABLE_LEARN AND Python_VERSION VERSION_LESS "3.7" )
  list( APPEND VIAME_PYTHON_BASIC_DEPS "wandb<=0.15.7" "fsspec<=2022.1.0" )
  if( WIN32 )
    list( APPEND VIAME_PYTHON_BASIC_DEPS "pyarrow==4.0.0" )
  else()
    list( APPEND VIAME_PYTHON_BASIC_DEPS "pyarrow==2.0.0" )
    list( APPEND VIAME_PYTHON_BASIC_DEPS "filelock==3.4.1" )
  endif()
endif()

if( ( WIN32 OR NOT VIAME_ENABLE_OPENCV ) AND
      ( VIAME_ENABLE_OPENCV OR
        VIAME_ENABLE_PYTORCH-MMDET OR
        VIAME_ENABLE_PYTORCH-NETHARN ) )
  if( WIN32 AND NOT VIAME_ENABLE_WIN32GUI )
    if( Python_VERSION VERSION_LESS "3.7" )
      list( APPEND VIAME_PYTHON_BASIC_DEPS "opencv-python-headless<=4.6.0.66" )
    else()
      list( APPEND VIAME_PYTHON_BASIC_DEPS "opencv-python-headless" )
    endif()
  else()
    if( Python_VERSION VERSION_LESS "3.7" )
      list( APPEND VIAME_PYTHON_BASIC_DEPS "opencv-python<=4.6.0.66" )
    else()
      list( APPEND VIAME_PYTHON_BASIC_DEPS "opencv-python" )
    endif()
  endif()
endif()

if( VIAME_ENABLE_KEYPOINTGUI )
  list( APPEND VIAME_PYTHON_BASIC_DEPS "msgpack" )
endif()

if( VIAME_ENABLE_PYTORCH )
  if( Python_VERSION VERSION_LESS "3.10" )
    list( APPEND VIAME_PYTHON_BASIC_DEPS "scikit-image==0.16.2" )
  else()
    list( APPEND VIAME_PYTHON_BASIC_DEPS "scikit-image==0.19.2" )
  endif()
endif()

if( VIAME_ENABLE_PYTORCH-MMDET OR VIAME_ENABLE_PYTORCH-NETHARN )
  list( APPEND VIAME_PYTHON_BASIC_DEPS "scikit-build" "async_generator" )
endif()

if( VIAME_ENABLE_PYTORCH-NETHARN AND VIAME_ENABLE_GDAL )
  if( WIN32 )
    list( APPEND VIAME_PYTHON_BASIC_DEPS "gdal==2.2.3" )
  else()
    list( APPEND VIAME_PYTHON_BASIC_DEPS "gdal" )
  endif()
endif()

if( VIAME_ENABLE_OPENCV OR VIAME_ENABLE_PYTORCH-NETHARN )
  list( APPEND VIAME_PYTHON_BASIC_DEPS "ubelt==1.3.3" "pygments")
  list( APPEND VIAME_PYTHON_BASIC_DEPS "ndsampler==0.6.7" "kwcoco==0.2.31" "pandas<=1.5.3" )
  list( APPEND VIAME_PYTHON_BASIC_DEPS "imageio==2.15.0" "networkx<=2.8.8" )

  if( Python_VERSION VERSION_LESS "3.9" )
    list( APPEND VIAME_PYTHON_BASIC_DEPS "bezier==2020.1.14" )
  endif()
endif()

if( Python_VERSION VERSION_LESS "3.7" AND
    ( VIAME_ENABLE_PYTORCH-PYSOT OR VIAME_ENABLE_SMQTK ) )
  list( APPEND VIAME_PYTHON_BASIC_DEPS "tensorboardX<=2.6.0" )
endif()

if( VIAME_ENABLE_PYTORCH AND VIAME_ENABLE_PYTORCH-INTERNAL )
  list( APPEND VIAME_PYTHON_BASIC_DEPS "pyyaml" )
endif()

if( VIAME_ENABLE_PYTORCH AND VIAME_ENABLE_PYTORCH-MMDET )
  if( WIN32 AND Python_VERSION VERSION_LESS "3.7" )
    list( APPEND VIAME_PYTHON_BASIC_DEPS "pycocotools-windows" )
  else()
    list( APPEND VIAME_PYTHON_BASIC_DEPS "pycocotools" )
  endif()
endif()

if( VIAME_ENABLE_PYTHON-INTERNAL AND UNIX )
  list( APPEND VIAME_PYTHON_BASIC_DEPS "backports.lzma" "backports.weakref" )
endif()

if( VIAME_ENABLE_TENSORFLOW )
  list( APPEND VIAME_PYTHON_BASIC_DEPS "humanfriendly" )
  set( TF_ARGS "" )

  if( VIAME_TENSORFLOW_VERSION VERSION_LESS "2.0" )
    if( VIAME_ENABLE_CUDA )
      set( TF_ARGS "-gpu" )
    endif()
  else()
    if( NOT VIAME_ENABLE_CUDA )
      set( TF_ARGS "-cpu" )
    endif()
  endif()

  set( TF_ARGS "${TF_ARGS}==${VIAME_TENSORFLOW_VERSION}" )
  list( APPEND VIAME_PYTHON_BASIC_DEPS "tensorflow${TF_ARGS}" )
endif()

# ------------------------------ ADD ANY ADV PYTHON DEPS HERE ------------------------------------
# Advanced python dependencies are installed individually due to special reqs

set( VIAME_PYTHON_ADV_DEPS python-deps )
set( VIAME_PYTHON_ADV_DEP_CMDS "custom-install" )

if( VIAME_ENABLE_KEYPOINTGUI )
  set( WX_VERSION "4.0.7" )

  list( APPEND VIAME_PYTHON_ADV_DEPS wxPython )

  if( UNIX )
    if( EXISTS "/etc/os-release" )
      ParseLinuxOSField( "ID" OS_ID )
    endif()

    execute_process( COMMAND lsb_release -cs
      OUTPUT_VARIABLE RELEASE_CODENAME
      OUTPUT_STRIP_TRAILING_WHITESPACE )

    if( "${OS_ID}" MATCHES "centos" )
      set( WXP_ARCHIVE https://extras.wxpython.org/wxPython4/extras/linux/gtk3/centos-7 )
      list( APPEND VIAME_PYTHON_ADV_DEP_CMDS "-U -f ${WXP_ARCHIVE} wxPython==${WX_VERSION}" )
    elseif( "${RELEASE_CODENAME}" MATCHES "xenial" )
      set( WXP_ARCHIVE https://extras.wxpython.org/wxPython4/extras/linux/gtk3/ubuntu-16.04 )
      list( APPEND VIAME_PYTHON_ADV_DEP_CMDS "-U -f ${WXP_ARCHIVE} wxPython==${WX_VERSION}" )
    else()
      list( APPEND VIAME_PYTHON_ADV_DEP_CMDS "wxPython==${WX_VERSION}" )
    endif()
  else()
    list( APPEND VIAME_PYTHON_ADV_DEP_CMDS "wxPython==${WX_VERSION}" )
  endif()
endif()

if( VIAME_ENABLE_PYTORCH AND NOT VIAME_ENABLE_PYTORCH-INTERNAL )
  list( APPEND VIAME_PYTHON_ADV_DEPS pytorch )

  set( PYTORCH_VERSION ${VIAME_PYTORCH_VERSION} )
  set( ARGS_TORCH )
  set( TORCHVISION_STR "" )

  if( VIAME_ENABLE_CUDA )
    set( CUDA_VER_STR "cu${CUDA_VERSION_MAJOR}${CUDA_VERSION_MINOR}" )
  else()
    set( CUDA_VER_STR "cpu" )
  endif()

  set( PYTORCH_ARCHIVE "https://download.pytorch.org/whl/${CUDA_VER_STR}" )

  if( NOT VIAME_ENABLE_PYTORCH-VIS-INTERNAL )
    if( PYTORCH_VERSION VERSION_GREATER_EQUAL "1.12.0" )
      set( TORCHVISION_STR "torchvision==0.13.0" )
    elseif( PYTORCH_VERSION VERSION_GREATER_EQUAL "1.10.0" )
      set( TORCHVISION_STR "torchvision==0.12.0" )
    elseif( PYTORCH_VERSION VERSION_GREATER_EQUAL "1.9.0" )
      set( TORCHVISION_STR "torchvision==0.10.1" )
    elseif( PYTORCH_VERSION VERSION_GREATER_EQUAL "1.8.2" )
      set( TORCHVISION_STR "torchvision==0.9.2" )
    elseif( PYTORCH_VERSION VERSION_GREATER_EQUAL "1.8.0" )
      set( TORCHVISION_STR "torchvision==0.9.0" )
    elseif( PYTORCH_VERSION VERSION_GREATER_EQUAL "1.7.0" )
      set( TORCHVISION_STR "torchvision==0.8.2" )
    elseif( PYTORCH_VERSION VERSION_GREATER_EQUAL "1.6.0" )
      set( TORCHVISION_STR "torchvision==0.7.0" )
    elseif( PYTORCH_VERSION VERSION_GREATER_EQUAL "1.4.0" )
      set( TORCHVISION_STR "torchvision==0.5.0" )
    else()
      set( TORCHVISION_STR "torchvision" )
    endif()
  endif()

  # Default case
  set( ARGS_TORCH "==${PYTORCH_VERSION} ${TORCHVISION_STR} --extra-index-url ${PYTORCH_ARCHIVE}" )

  # Account for either direct link to package or default case
  string( FIND "${ARGS_TORCH}" "https://" TMP_VAR )
  if( "${TMP_VAR}" EQUAL 0 )
    list( APPEND VIAME_PYTHON_ADV_DEP_CMDS "${ARGS_TORCH}" )
  else()
    list( APPEND VIAME_PYTHON_ADV_DEP_CMDS "torch${ARGS_TORCH}" )
  endif()
endif()

# ------------------------------------- INSTALL ROUTINES -----------------------------------------

set( VIAME_PYTHON_DEPS_DEPS fletch )

list( LENGTH VIAME_PYTHON_ADV_DEPS DEP_COUNT )
math( EXPR DEP_COUNT "${DEP_COUNT} - 1" )

foreach( ID RANGE ${DEP_COUNT} )

  list( GET VIAME_PYTHON_ADV_DEPS ${ID} DEP )

  set( VIAME_PROJECT_LIST ${VIAME_PROJECT_LIST} ${DEP} )

  if( "${DEP}" STREQUAL "python-deps" )
    set( PYTHON_LIB_DEPS ${VIAME_PYTHON_DEPS_DEPS} )
    set( CMD ${VIAME_PYTHON_BASIC_DEPS} )
  else()
    set( PYTHON_LIB_DEPS ${VIAME_PYTHON_DEPS_DEPS} python-deps )
    list( GET VIAME_PYTHON_ADV_DEP_CMDS ${ID} CMD )
  endif()

  set( PYTHON_DEP_PIP_CMD pip install --user ${CMD} )
  string( REPLACE " " ";" PYTHON_DEP_PIP_CMD "${PYTHON_DEP_PIP_CMD}" )

  set( PYTHON_DEP_BUILD
    ${CMAKE_COMMAND} -E env "${PYTHON_DEP_ENV_VARS}"
      ${Python_EXECUTABLE} -m ${PYTHON_DEP_PIP_CMD}
    )

  if( "${DEP}" STREQUAL "pytorch" )
    set( PYTHON_DEP_INSTALL ${CMAKE_COMMAND}
      -DVIAME_PYTHON_BASE:PATH=${VIAME_PYTHON_INSTALL}
      -DVIAME_PATCH_DIR:PATH=${VIAME_SOURCE_DIR}/packages/patches
      -DVIAME_PYTORCH_VERSION:STRING=${VIAME_PYTORCH_VERSION}
      -P ${VIAME_SOURCE_DIR}/cmake/custom_install_pytorch.cmake )
  elseif( "${DEP}" STREQUAL "python-deps" )
    set( PYTHON_DEP_INSTALL ${CMAKE_COMMAND}
      -DVIAME_PYTHON_BASE:PATH=${VIAME_PYTHON_INSTALL}
      -DVIAME_PATCH_DIR:PATH=${VIAME_SOURCE_DIR}/packages/patches
      -DVIAME_PYTHON_VERSION:STRING=${Python_VERSION}
      -P ${VIAME_SOURCE_DIR}/cmake/custom_install_python_deps.cmake )
  else()
    set( PYTHON_DEP_INSTALL "" )
  endif()

  ExternalProject_Add( ${DEP}
    DEPENDS ${PYTHON_LIB_DEPS}
    PREFIX ${VIAME_BUILD_PREFIX}
    SOURCE_DIR ${VIAME_CMAKE_DIR}
    USES_TERMINAL_BUILD 1
    CONFIGURE_COMMAND ""
    BUILD_COMMAND ${PYTHON_DEP_BUILD}
    INSTALL_COMMAND "${PYTHON_DEP_INSTALL}"
    INSTALL_DIR ${VIAME_INSTALL_PREFIX}
    LIST_SEPARATOR "----"
    )
endforeach()

# ------------------------------------- PYMOTMETRICS -----------------------------------------

# TODO: refactor this and make more generic for any python-utils requiring custom whl builds

set( VIAME_PROJECT_LIST ${VIAME_PROJECT_LIST} pymotmetrics )

set( PROJECT_DEPS fletch python-deps )

if( VIAME_SYMLINK_PYTHON )
  set( LIBRARY_PIP_BUILD_CMD
    ${Python_EXECUTABLE} setup.py build )
  set( LIBRARY_PIP_INSTALL_CMD
    ${Python_EXECUTABLE} -m pip install --user -e . )
else()
  set( LIBRARY_PIP_BUILD_DIR ${VIAME_BUILD_PREFIX}/src/pymotmetrics-build )
  CreateDirectory( ${LIBRARY_PIP_BUILD_DIR} )

  set( LIBRARY_PIP_BUILD_CMD
    ${Python_EXECUTABLE} setup.py build_ext
      --include-dirs="${VIAME_INSTALL_PREFIX}/include"
      --library-dirs="${VIAME_INSTALL_PREFIX}/lib"
      --inplace bdist_wheel -d ${LIBRARY_PIP_BUILD_DIR} )
  set( LIBRARY_PIP_INSTALL_CMD
    ${CMAKE_COMMAND}
      -DPYTHON_EXECUTABLE=${Python_EXECUTABLE}
      -DPython_EXECUTABLE=${Python_EXECUTABLE}
      -DWHEEL_DIR=${LIBRARY_PIP_BUILD_DIR}
      -P ${VIAME_CMAKE_DIR}/install_python_wheel.cmake )
endif()

set( LIBRARY_PYTHON_BUILD
  ${CMAKE_COMMAND} -E env "${PYTHON_DEP_ENV_VARS}"
  ${LIBRARY_PIP_BUILD_CMD} )
set( LIBRARY_PYTHON_INSTALL
  ${CMAKE_COMMAND} -E env "${PYTHON_DEP_ENV_VARS}"
  ${LIBRARY_PIP_INSTALL_CMD} )

ExternalProject_Add( pymotmetrics
  DEPENDS ${PROJECT_DEPS}
  PREFIX ${VIAME_BUILD_PREFIX}
  SOURCE_DIR ${VIAME_PACKAGES_DIR}/python-utils/pymotmetrics
  BUILD_IN_SOURCE 1
  CONFIGURE_COMMAND ""
  BUILD_COMMAND ${LIBRARY_PYTHON_BUILD}
  INSTALL_COMMAND ${LIBRARY_PYTHON_INSTALL}
  LIST_SEPARATOR "----"
  )

