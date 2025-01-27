# vibrant External Project
#
# Required symbols are:
#   VIAME_BUILD_PREFIX - where packages are built
#   VIAME_BUILD_INSTALL_PREFIX - directory install target
#   VIAME_PACKAGES_DIR - location of git submodule packages
#   VIAME_ARGS_COMMON -
##

set( VIAME_PROJECT_LIST ${VIAME_PROJECT_LIST} burnout )

set( BURNOUT_CXX_FLAGS "${CMAKE_CXX_FLAGS} -std=c++0x" )

ExternalProject_Add(burnout
  DEPENDS fletch
  PREFIX ${VIAME_BUILD_PREFIX}
  SOURCE_DIR ${VIAME_PACKAGES_DIR}/burn-out
  USES_TERMINAL_BUILD 1
  CMAKE_GENERATOR ${gen}
  CMAKE_ARGS
    ${VIAME_ARGS_COMMON}
    ${VIAME_ARGS_fletch}
    ${VIAME_ARGS_VXL}
    ${VIAME_ARGS_Qt}

    -DBUILD_TESTING:BOOL=OFF
    -DVIDTK_BUILD_TESTS:BOOL=OFF

    -DVIDTK_ENABLE_OPENCV:BOOL=${VIAME_ENABLE_OPENCV}
    -DVIDTK_ENABLE_QT:BOOL=OFF
    -DVIDTK_ENABLE_GDAL:BOOL=OFF

    -DBOOST_ROOT:PATH=${VIAME_BUILD_INSTALL_PREFIX}
    -DBoost_DIR:PATH=${VIAME_BUILD_INSTALL_PREFIX}
    -DBoost_INCLUDE_DIRS:PATH=${VIAME_BUILD_INSTALL_PREFIX}/include
    -DBoost_INCLUDE_DIR:PATH=${VIAME_BUILD_INSTALL_PREFIX}/include
    -DBoost_LIBRARY_DIR:PATH=${VIAME_BUILD_INSTALL_PREFIX}/lib
    -DBoost_LIBRARY_DIR_DEBUG:PATH=${VIAME_BUILD_INSTALL_PREFIX}/lib
    -DBoost_LIBRARY_DIR_RELEASE:PATH=${VIAME_BUILD_INSTALL_PREFIX}/lib

    -DCMAKE_CXX_FLAGS:STRING=${BURNOUT_CXX_FLAGS}

  INSTALL_DIR ${VIAME_BUILD_INSTALL_PREFIX}
  )

if ( VIAME_FORCEBUILD )
ExternalProject_Add_Step(burnout forcebuild
  COMMAND ${CMAKE_COMMAND}
    -E remove ${VIAME_BUILD_PREFIX}/src/burnout-stamp/burnout-build
  COMMENT "Removing build stamp file for build update (forcebuild)."
  DEPENDEES configure
  DEPENDERS build
  ALWAYS 1
  )
endif()

set(VIAME_ARGS_burnout
  -Dburnout_DIR:PATH=${VIAME_BUILD_PREFIX}/src/burnout-build
  -Dvidtk_DIR:PATH=${VIAME_BUILD_PREFIX}/src/burnout-build
  )
