# scallop_tk External Project
#
# Required symbols are:
#   VIAME_BUILD_PREFIX - where packages are built
#   VIAME_BUILD_INSTALL_PREFIX - directory install target
#   VIAME_PACKAGES_DIR - location of git submodule packages
#   VIAME_ARGS_COMMON -
##

set( VIAME_PROJECT_LIST ${VIAME_PROJECT_LIST} scallop_tk )

if( WIN32 )
  set( ScallopTK_BUILD_SHARED
    -DBUILD_SHARED_LIBS:BOOL=OFF
  )
  set( ScallopTK_HDF5_DIRS
    -DHDF5_DIR:PATH=${VIAME_BUILD_INSTALL_PREFIX}/cmake
    -DHDF5_DIFF_EXECUTABLE:PATH=${VIAME_BUILD_INSTALL_PREFIX}/bin/h5diff.exe
  )
else()
  set( ScallopTK_BUILD_SHARED
    -DBUILD_SHARED_LIBS:BOOL=ON
  )
endif()

if( VIAME_ENABLE_CUDA )
  set( SCALLOP_TK_CPU_ONLY OFF )
else()
  set( SCALLOP_TK_CPU_ONLY ON )
endif()

if(VIAME_FORCE_CUDA_CSTD98)
  set( ScallopTK_CXXFLAGS_OVERRIDE
    -DCMAKE_CXX_FLAGS=-std=c++98 )
else()
  set( ScallopTK_CXXFLAGS_OVERRIDE )
endif()

ExternalProject_Add(scallop_tk
  DEPENDS fletch
  PREFIX ${VIAME_BUILD_PREFIX}
  SOURCE_DIR ${VIAME_PACKAGES_DIR}/scallop-tk
  USES_TERMINAL_BUILD 1
  CMAKE_GENERATOR ${gen}
  CMAKE_CACHE_ARGS
    ${VIAME_ARGS_COMMON}
    ${VIAME_ARGS_fletch}
    ${ScallopTK_BUILD_SHARED}
    ${ScallopTK_HDF5_DIRS}
    ${ScallopTK_CXXFLAGS_OVERRIDE}
    -DVC_TOOLNAMES:BOOL=ON
    -DBUILD_TOOLS:BOOL=ON
    -DBUILD_TESTS:BOOL=OFF
    -DDOWNLOAD_MODELS:BOOL=${VIAME_DOWNLOAD_MODELS-HABCAM}
    -DMODEL_INSTALL_DIR:PATH=configs/pipelines/models/scallop_tk
  INSTALL_DIR ${VIAME_BUILD_INSTALL_PREFIX}
  )

if ( VIAME_FORCEBUILD )
ExternalProject_Add_Step(scallop_tk forcebuild
  COMMAND ${CMAKE_COMMAND}
    -E remove ${VIAME_BUILD_PREFIX}/src/scallop_tk-stamp/scallop_tk-build
  COMMENT "Removing build stamp file for build update (forcebuild)."
  DEPENDEES configure
  DEPENDERS build
  ALWAYS 1
  )
endif()

set(VIAME_ARGS_scallop_tk
  -DScallopTK_DIR:PATH=${VIAME_BUILD_PREFIX}/src/scallop_tk-build
  )
