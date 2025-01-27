# Tensorflow Internal Project Add
#
# Required symbols are:
#   VIAME_BUILD_PREFIX - where packages are built
#   VIAME_INSTALL_PREFIX - directory install target
#   VIAME_PACKAGES_DIR - location of git submodule packages
#   VIAME_ARGS_COMMON -
##

CreateDirectory( ${VIAME_BUILD_PREFIX}/src/tensorflow-build )

set( TENSORFLOW_ENV_VARS )

if( NOT VIAME_ENABLE_PYTORCH )
  if( WIN32 )
    set( PROTOC_PATH "${VIAME_PYTHON_INSTALL}/site-packages/torch/bin/protoc.exe" )
  else()
    set( PROTOC_PATH "${VIAME_PYTHON_INSTALL}/site-packages/torch/bin/protoc" )
  endif()
else()
  if( WIN32 )
    set( PROTOC_PATH "protoc.exe" )
  else()
    set( PROTOC_PATH "protoc" )
  endif()
endif()

if( WIN32 )
  set( EXTRA_INCLUDE_DIRS "${VIAME_INSTALL_PREFIX}/include;$ENV{INCLUDE}" )
  set( EXTRA_LIBRARY_DIRS "${VIAME_INSTALL_PREFIX}/lib;$ENV{LIB}" )

  string( REPLACE ";" "----" VIAME_PYTHON_PATH "${VIAME_PYTHON_PATH}" )
  string( REPLACE ";" "----" EXTRA_INCLUDE_DIRS "${EXTRA_INCLUDE_DIRS}" )
  string( REPLACE ";" "----" EXTRA_LIBRARY_DIRS "${EXTRA_LIBRARY_DIRS}" )

  list( APPEND TENSORFLOW_ENV_VARS "INCLUDE=${EXTRA_INCLUDE_DIRS}" )
  list( APPEND TENSORFLOW_ENV_VARS "LIB=${EXTRA_LIBRARY_DIRS}" )
else()
  list( APPEND TENSORFLOW_ENV_VARS "CPPFLAGS=-I${VIAME_INSTALL_PREFIX}/include" )
  list( APPEND TENSORFLOW_ENV_VARS "LDFLAGS=-L${VIAME_INSTALL_PREFIX}/lib" )
  list( APPEND TENSORFLOW_ENV_VARS "CC=${CMAKE_C_COMPILER}" )
  list( APPEND TENSORFLOW_ENV_VARS "CXX=${CMAKE_CXX_COMPILER}" )
  list( APPEND TENSORFLOW_ENV_VARS "PATH=${VIAME_EXECUTABLES_PATH}" )
endif()

list( APPEND TENSORFLOW_ENV_VARS "PYTHONPATH=${VIAME_PYTHON_PATH}" )
list( APPEND TENSORFLOW_ENV_VARS "PYTHONUSERBASE=${VIAME_INSTALL_PREFIX}" )

if( VIAME_ENABLE_TENSORFLOW-MODELS )
  if( VIAME_PYTHON_SYMLINK )
    set( LIBRARY_PIP_BUILD_CMD
      ${Python_EXECUTABLE} setup.py build )
    set( LIBRARY_PIP_INSTALL_CMD
      ${Python_EXECUTABLE} -m pip install --user -e . )
  else()
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
        -DWHEEL_DIR=${LIBRARY_PIP_BUILD_DIR}
        -P ${VIAME_CMAKE_DIR}/install_python_wheel.cmake )
  endif()

  set( LIBRARY_PYTHON_BUILD
    ${CMAKE_COMMAND} -E env "${TENSORFLOW_ENV_VARS}"
    "TMPDIR=${LIBRARY_PIP_TMP_DIR}"
    ${LIBRARY_PIP_BUILD_CMD} )
  set( LIBRARY_PYTHON_INSTALL
    ${CMAKE_COMMAND} -E env "${TENSORFLOW_ENV_VARS}"
    "TMPDIR=${LIBRARY_PIP_TMP_DIR}"
    ${LIBRARY_PIP_INSTALL_CMD} )

  set( PROJECT_DEPS fletch python-deps )

  if( VIAME_ENABLE_SMQTK )
    set( PROJECT_DEPS ${PROJECT_DEPS} smqtk )
  endif()

  ExternalProject_Add( tensorflow-models
    DEPENDS ${PROJECT_DEPS}
    PREFIX ${VIAME_BUILD_PREFIX}
    SOURCE_DIR ${LIBRARY_LOCATION}
    BUILD_IN_SOURCE 1
    CONFIGURE_COMMAND ""
    BUILD_COMMAND ${LIBRARY_PYTHON_BUILD}
    INSTALL_COMMAND ${LIBRARY_PYTHON_INSTALL}
    LIST_SEPARATOR "----"
    )

  if( VIAME_FORCEBUILD )
    ExternalProject_Add_Step( tensorflow-models forcebuild
      COMMAND ${CMAKE_COMMAND}
        -E remove ${VIAME_BUILD_PREFIX}/src/{LIB}-stamp
      COMMENT "Removing build stamp file for build update (forcebuild)."
      DEPENDEES configure
      DEPENDERS build
      ALWAYS 1
      )
  endif()
endif()
