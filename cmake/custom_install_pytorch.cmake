message( "Running pytorch auxiliary install" )

if( WIN32 )

  # Patches directly to pytorch
  set( TORCH_DIR ${VIAME_PYTHON_BASE}/site-packages/torch )

  if( NOT EXISTS ${TORCH_DIR} )
    set( TORCH_DIR ${VIAME_PYTHON_BASE}/dist-packages/torch )
  endif()

  if( VIAME_PYTORCH_VERSION VERSION_EQUAL "1.7.1" )
    set( PATCH ${VIAME_PATCH_DIR}/pytorch/mmcv-win32-1.7.1/include )
  elseif( VIAME_PYTORCH_VERSION VERSION_EQUAL "1.4.0" )
    set( PATCH ${VIAME_PATCH_DIR}/pytorch/mmcv-win32-1.4.0/include )
  endif()

  if( EXISTS ${TORCH_DIR} )
    file( COPY ${PATCH}
          DESTINATION ${TORCH_DIR} )
  endif()

  # Patches to dependencies brought in by pytorch
  if( VIAME_PYTORCH_VERSION VERSION_EQUAL "2.5.1" AND
      EXISTS ${VIAME_PYTHON_BASE}/site-packages/iopath )
    file( COPY ${VIAME_PATCH_DIR}/iopath
          DESTINATION ${VIAME_PYTHON_BASE}/site-packages )
  endif()

endif()

message( "Done" )
