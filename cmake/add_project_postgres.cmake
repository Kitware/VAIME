# Postgres is provided via fletch for only linux but not windows
if( WIN32 )
  include( ExternalProject )

  set( VIAME_POSTGRES_URL https://data.kitware.com/api/v1/item/5ba55cd58d777f06b900d726/download )
  set( VIAME_POSTGRES_MD5 7648e722fda0fcc47c96ef8093a369be )
  set( VIAME_POSTGRES_FILENAME postgresql-9.5.1-1-windows-x64-binaries.zip )

  set( VIAME_POSTGRES_DIR ${VIAME_BUILD_PREFIX}/src/postgres )

  ExternalProject_Add( postgres
    DEPENDS fletch
    URL ${VIAME_POSTGRES_URL}
    URL_MD5 ${VIAME_POSTGRES_MD5}
    DOWNLOAD_DIR ${VIAME_DOWNLOAD_DIR}
    DOWNLOAD_NAME ${VIAME_POSTGRES_FILENAME}
    PREFIX ${VIAME_BUILD_PREFIX}
    CONFIGURE_COMMAND ""
    BUILD_COMMAND ""
    INSTALL_COMMAND ${CMAKE_COMMAND} -E copy_directory ${VIAME_POSTGRES_DIR}/bin ${VIAME_BUILD_INSTALL_PREFIX}/bin
      COMMAND ${CMAKE_COMMAND} -E copy_directory ${VIAME_POSTGRES_DIR}/lib ${VIAME_BUILD_INSTALL_PREFIX}/lib
      COMMAND ${CMAKE_COMMAND} -E copy_directory ${VIAME_POSTGRES_DIR}/share ${VIAME_BUILD_INSTALL_PREFIX}/share
    )
endif()
