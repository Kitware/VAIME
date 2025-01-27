# SMQTK External Project
#
# Required symbols are:
#   VIAME_BUILD_PREFIX - where packages are built
#   VIAME_INSTALL_PREFIX - directory install target
#   VIAME_PACKAGES_DIR - location of git submodule packages
#   VIAME_ARGS_COMMON -
##

set( VIAME_PROJECT_LIST ${VIAME_PROJECT_LIST} smqtk )

set( SMQTK_DEPENDS fletch python-deps )

if( VIAME_ENABLE_PYTHON )
  FormatPassdowns( "Python" VIAME_PYTHON_FLAGS )
endif()

if( VIAME_ENABLE_CUDA )
  FormatPassdowns( "CUDA" VIAME_CUDA_FLAGS )
endif()

if( VIAME_ENABLE_POSTGRESQL AND WIN32 )
  list( APPEND SMQTK_DEPENDS postgres )
endif()

set( SMQTK_PIP_CMD )
set( SMQTK_PIP_OPT )

if( VIAME_PYTHON_SYMLINK )
  if( VIAME_ENABLE_POSTGRESQL )
    set( SMQTK_PIP_OPT "[postgres]" )
  endif()
  set( SMQTK_PIP_CMD
    pip install --user -e .${SMQTK_PIP_OPT} )
else()
  # This is only required for no symlink install without a -e with older
  # versions of pip, for never versions the above command works with no -e
  if( VIAME_ENABLE_POSTGRESQL )
    set( SMQTK_PIP_OPT "\#egg=smqtk[postgres]" )
  endif()
  set( SMQTK_PIP_CMD
    pip install --user file://${VIAME_PACKAGES_DIR}/smqtk${SMQTK_PIP_OPT} )
endif()

set( SMQTK_PYTHON_INSTALL
  ${CMAKE_COMMAND} -E env "${PYTHON_DEP_ENV_VARS}"
    ${Python_EXECUTABLE} -m ${SMQTK_PIP_CMD}
  )

ExternalProject_Add( smqtk
  DEPENDS ${SMQTK_DEPENDS}
  PREFIX ${VIAME_BUILD_PREFIX}
  SOURCE_DIR ${VIAME_PACKAGES_DIR}/smqtk
  USES_TERMINAL_BUILD 1
  CMAKE_GENERATOR ${gen}
  CMAKE_CACHE_ARGS
    -DSMQTK_BUILD_EXAMPLES:BOOL=OFF
    -DSMQTK_BUILD_LIBSVM:BOOL=ON
    -DSMQTK_BUILD_FLANN:BOOL=OFF
    -DSMQTK_INSTALL_SETUP_SCRIPT:BOOL=OFF
    ${VIAME_ARGS_COMMON}
    ${VIAME_ARGS_fletch}
    ${VIAME_PYTHON_FLAGS}
    ${VIAME_CUDA_FLAGS}

  INSTALL_DIR ${VIAME_INSTALL_PREFIX}
  LIST_SEPARATOR "----"
  )

ExternalProject_Add_Step(smqtk install_python
  WORKING_DIRECTORY ${VIAME_PACKAGES_DIR}/smqtk
  COMMAND ${SMQTK_PYTHON_INSTALL}
  COMMENT "Installing SMQTK python files."
  DEPENDEES build
  )

ExternalProject_Add_Step(smqtk install_cleanup
  WORKING_DIRECTORY ${VIAME_PACKAGES_DIR}/smqtk
  COMMAND ${CMAKE_COMMAND}
    -DVIAME_CMAKE_DIR:PATH=${VIAME_CMAKE_DIR}
    -DVIAME_PACKAGES_DIR:PATH=${VIAME_PACKAGES_DIR}
    -DVIAME_BUILD_PREFIX:PATH=${VIAME_BUILD_PREFIX}
    -DVIAME_INSTALL_PREFIX:PATH=${VIAME_INSTALL_PREFIX}
    -DVIAME_ENABLE_SMQTK=${VIAME_ENABLE_SMQTK}
    -DVIAME_PYTHON_INSTALL=${VIAME_PYTHON_INSTALL}
    -P ${VIAME_SOURCE_DIR}/cmake/custom_install_smqtk.cmake
  COMMENT "Performing SMQTK Cleanup."
  DEPENDEES build
  )

if ( VIAME_FORCEBUILD )
ExternalProject_Add_Step(smqtk forcebuild
  COMMAND ${CMAKE_COMMAND}
    -E remove ${VIAME_BUILD_PREFIX}/src/smqtk-stamp/smqtk-build
  COMMENT "Removing build stamp file for build update (forcebuild)."
  DEPENDEES configure
  DEPENDERS build
  ALWAYS 1
  )
endif()

set(VIAME_ARGS_SMQTK
  -DSMQTK_DIR:PATH=${VIAME_BUILD_PREFIX}/src/smqtk-build
  )
