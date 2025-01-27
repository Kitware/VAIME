REM -------------------------------------------------------------------------------------------------------
REM Setup Paths
REM -------------------------------------------------------------------------------------------------------

SET "VIAME_SOURCE_DIR=C:\workspace\VIAME-Windows-GPU-Release"
SET "OUTPUT_FILE=VIAME-v1.0.0-Windows-64Bit.zip"

REM Make sure to have all of these things installed (and cuDNN in CUDA)

SET "CMAKE_ROOT=C:\Program Files\CMake"
SET "GIT_ROOT=C:\Program Files\Git"
SET "7ZIP_ROOT=C:\Program Files\7-Zip"
SET "ZLIB_ROOT=C:\Program Files\ZLib"
SET "NVIDIA_ROOT=C:\Program Files (x86)\NVIDIA Corporation"
SET "CUDA_ROOT=C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.4"

SET "WIN_ROOT=C:\Windows"
SET "WIN32_ROOT=%WIN_ROOT%\System32"
SET "WIN64_ROOT=%WIN_ROOT%\SysWOW64"

REM Do not modify the below unless you are changing python versions or have alternatively modified
REM the build and install directories in cmake or the platforms.cmake file

SET "VIAME_BUILD_DIR=%VIAME_SOURCE_DIR%\build"
SET "VIAME_INSTALL_DIR=%VIAME_BUILD_DIR%\install"

SET "PYTHON_SUBDIR=lib\python3.10"

SET "PATH=%WIN_ROOT%;%WIN32_ROOT%;%WIN32_ROOT%\Wbem;%WIN32_ROOT%\WindowsPowerShell\v1.0;%WIN32_ROOT%\OpenSSH"
SET "PATH=%CUDA_ROOT%\bin;%CUDA_ROOT%\libnvvp;%NVIDIA_ROOT%\PhysX\Common;%NVIDIA_ROOT%\NVIDIA NvDLISR;%PATH%"
SET "PATH=%GIT_ROOT%\cmd;%CMAKE_ROOT%\bin;%PATH%"
SET "PATH=%VIAME_INSTALL_DIR%\bin;%PATH%"
SET "PYTHONHOME=%VIAME_INSTALL_DIR%\%PYTHON_SUBDIR%"
SET "PYTHONPATH=%VIAME_INSTALL_DIR%\%PYTHON_SUBDIR%;%VIAME_INSTALL_DIR%\%PYTHON_SUBDIR%\site-packages"

REM -------------------------------------------------------------------------------------------------------
REM Perform Actual Build
REM -------------------------------------------------------------------------------------------------------

REM If running locally instead of on Jenkins server, file jenkins_dashboard.cmake should be a renamed
REM version of the file located at jenkins/CTestBuildOnlyPipeline, with 'platform.cmake' in the
REM file pointed to build_server_windows.cmake (or alternatively the latter renamed to platform.cmake).

"C:\Program Files\CMake\bin\ctest.exe" -S jenkins_dashboard.cmake -VV

REM -------------------------------------------------------------------------------------------------------
REM Final Install Generation Hacks Until Handled Better in VIAME CMake
REM -------------------------------------------------------------------------------------------------------

MOVE "%MISSING_SVM_DLL%" %VIAME_INSTALL_DIR%\bin
MOVE "%MISSING_DNET_EXE%" %VIAME_INSTALL_DIR%\bin

COPY "%WIN32_ROOT%\msvcr100.dll" %VIAME_INSTALL_DIR%\bin
COPY "%WIN32_ROOT%\vcruntime140_1.dll" %VIAME_INSTALL_DIR%\bin
COPY "%WIN64_ROOT%\vcomp140.dll" %VIAME_INSTALL_DIR%\bin
COPY "%WIN64_ROOT%\msvcr120.dll" %VIAME_INSTALL_DIR%\bin
COPY "%ZLIB_ROOT%\dll_x64\zlibwapi.dll" %VIAME_INSTALL_DIR%\bin

DEL "%VIAME_INSTALL_DIR%\%PYTHON_SUBDIR%\site-packages\torch\lib\cu*"

COPY "%CUDA_ROOT%\bin\cublas64_11.dll" %VIAME_INSTALL_DIR%\bin
COPY "%CUDA_ROOT%\bin\cublasLt64_11.dll" %VIAME_INSTALL_DIR%\bin
COPY "%CUDA_ROOT%\bin\cudart64_124.dll" %VIAME_INSTALL_DIR%\bin
COPY "%CUDA_ROOT%\bin\cudnn_adv_infer64_9.dll" %VIAME_INSTALL_DIR%\bin
COPY "%CUDA_ROOT%\bin\cudnn_adv_train64_9.dll" %VIAME_INSTALL_DIR%\bin
COPY "%CUDA_ROOT%\bin\cudnn_cnn_infer64_9.dll" %VIAME_INSTALL_DIR%\bin
COPY "%CUDA_ROOT%\bin\cudnn_cnn_train64_9.dll" %VIAME_INSTALL_DIR%\bin
COPY "%CUDA_ROOT%\bin\cudnn_ops_infer64_9.dll" %VIAME_INSTALL_DIR%\bin
COPY "%CUDA_ROOT%\bin\cudnn_ops_train64_9.dll" %VIAME_INSTALL_DIR%\bin
COPY "%CUDA_ROOT%\bin\cudnn64_9.dll" %VIAME_INSTALL_DIR%\bin
COPY "%CUDA_ROOT%\bin\cufft64_10.dll" %VIAME_INSTALL_DIR%\bin
COPY "%CUDA_ROOT%\bin\cufftw64_10.dll" %VIAME_INSTALL_DIR%\bin
COPY "%CUDA_ROOT%\bin\curand64_10.dll" %VIAME_INSTALL_DIR%\bin
COPY "%CUDA_ROOT%\bin\cusolver64_11.dll" %VIAME_INSTALL_DIR%\bin
COPY "%CUDA_ROOT%\bin\cusolverMg64_11.dll" %VIAME_INSTALL_DIR%\bin
COPY "%CUDA_ROOT%\bin\cusparse64_11.dll" %VIAME_INSTALL_DIR%\bin

REM -------------------------------------------------------------------------------------------------------
REM Generate Final Zip File
REM -------------------------------------------------------------------------------------------------------

MOVE "%VIAME_INSTALL_DIR%" "%VIAME_BUILD_DIR%\VIAME"

"%7ZIP_ROOT%\7z.exe" a "%VIAME_BUILD_DIR%/%OUTPUT_FILE%" "%VIAME_BUILD_DIR%/VIAME

MOVE "%VIAME_BUILD_DIR%\VIAME" "%VIAME_INSTALL_DIR%"
