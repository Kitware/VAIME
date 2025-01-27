# Install onnx python
set( ONNXRUNTIME_PYTHON onnxruntime )
set( ONNXRUNTIME_PIP_BUILD_DIR ${VIAME_BUILD_PREFIX}/src/${ONNXRUNTIME_PYTHON}-build )
CreateDirectory( ${ONNXRUNTIME_PIP_BUILD_DIR} )
set( ONNXRUNTIME_PIP_TMP_DIR ${VIAME_BUILD_PREFIX}/src/${ONNXRUNTIME_PYTHON}-tmp )
CreateDirectory( ${ONNXRUNTIME_PIP_TMP_DIR} )

set( ONNXRUNTIME_PIP_INSTALL_CMD "" )
if( VIAME_SYMLINK_PYTHON )
    set( ONNXRUNTIME_PIP_INSTALL_CMD
      ${Python_EXECUTABLE} -m pip install --user -e . )
else()
    set( ONNXRUNTIME_PIP_INSTALL_CMD
        ${CMAKE_COMMAND}
            -DPYTHON_EXECUTABLE=${Python_EXECUTABLE}
            -DPython_EXECUTABLE=${Python_EXECUTABLE}
            -DWHEEL_DIR=${ONNXRUNTIME_PIP_BUILD_DIR}
            -P ${VIAME_CMAKE_DIR}/install_python_wheel.cmake )
endif()

# Instead of building the wheel, we download it directly in the build folder
set( ONNXRUNTIME_PYTHON_DOWNLOAD ${Python_EXECUTABLE} -m pip download
  --no-deps onnxruntime==1.12.1 -d "${ONNXRUNTIME_PIP_BUILD_DIR}" )
set( ONNXRUNTIME_PYTHON_INSTALL ${CMAKE_COMMAND} -E env "${PYTHON_DEP_ENV_VARS}"
  "TMPDIR=${ONNXRUNTIME_PIP_TMP_DIR}" ${ONNXRUNTIME_PIP_INSTALL_CMD} )

ExternalProject_Add( ${ONNXRUNTIME_PYTHON}
  PREFIX ${VIAME_BUILD_PREFIX}
  DOWNLOAD_COMMAND ${ONNXRUNTIME_PYTHON_DOWNLOAD}
  SOURCE_DIR ""
  BUILD_IN_SOURCE 1
  PATCH_COMMAND ""
  CONFIGURE_COMMAND ""
  BUILD_COMMAND ""
  INSTALL_COMMAND ${ONNXRUNTIME_PYTHON_INSTALL}
  LIST_SEPARATOR "----"
  )

# Install onnx libs
set( ONNXRUNTIME_LIBS_URL "" )
set( ONNXRUNTIME_LIBS_DOWNLOAD_DIR ${VIAME_BUILD_PREFIX}/src/onnxruntimelibs )
set( ONNXRUNTIME_LIBS_INSTALL_DIR ${VIAME_INSTALL_PREFIX}/lib/${VIAME_PYTHON_STRING}/site-packages/onnxruntime )
if( UNIX )
  set(ONNXRUNTIME_LIBS_URL https://github.com/microsoft/onnxruntime/releases/download/v1.12.1/onnxruntime-linux-x64-1.12.1.tgz )
elseif( WIN32 )
  set( ONNXRUNTIME_LIBS_URL https://github.com/microsoft/onnxruntime/releases/download/v1.12.1/onnxruntime-win-x64-1.12.1.zip )
else()
  message(FATAL_ERROR "Cannot download ONNXRUNTIME because system is not supported")
endif()


set( ONNXRUNTIMELIBS_DEPS ${ONNXRUNTIME_PYTHON} )
set( ONNXRUNTIMELIBS_INSTALL_COMMAND ${CMAKE_COMMAND} -E copy_directory
  ${ONNXRUNTIME_LIBS_DOWNLOAD_DIR} ${ONNXRUNTIME_LIBS_INSTALL_DIR}/onnxruntimelibs )

ExternalProject_Add( onnxruntimelibs
  DEPENDS ${ONNXRUNTIMELIBS_DEPS}
  SOURCE_DIR ""
  URL ${ONNXRUNTIME_LIBS_URL}
  PREFIX ${VIAME_BUILD_PREFIX}
  CONFIGURE_COMMAND ""
  BUILD_COMMAND ""
  INSTALL_COMMAND ${ONNXRUNTIMELIBS_INSTALL_COMMAND}
  )
