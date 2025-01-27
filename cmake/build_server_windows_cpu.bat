REM -------------------------------------------------------------------------------------------------------
REM Setup Paths
REM -------------------------------------------------------------------------------------------------------

SET "VIAME_SOURCE_DIR=C:\workspace\VIAME-Windows-CPU-Release"
SET "OUTPUT_FILE=VIAME-CPU-v1.0.0-Windows-64Bit.zip"

REM Make sure to have all of these things installed

SET "CMAKE_ROOT=C:\Program Files\CMake"
SET "GIT_ROOT=C:\Program Files\Git"
SET "ZIP_ROOT=C:\Program Files\7-Zip"
SET "ZLIB_ROOT=C:\Program Files\ZLib"

SET "WIN_ROOT=C:\Windows"
SET "WIN32_ROOT=%WIN_ROOT%\System32"
SET "WIN64_ROOT=%WIN_ROOT%\SysWOW64"
SET "VDIST_ROOT=C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\VC\Redist\MSVC\14.29.30133\x64\Microsoft.VC142.OpenMP"

REM Do not modify the below unless you are changing python versions or have alternatively modified
REM the build and install directories in cmake or the platforms.cmake file

SET "VIAME_BUILD_DIR=%VIAME_SOURCE_DIR%\build"
SET "VIAME_INSTALL_DIR=%VIAME_BUILD_DIR%\install"

SET "PYTHON_SUBDIR=lib\python3.10"
SET "ZLIB_BUILD_DIR=%VIAME_BUILD_DIR%\build\src\fletch-build\build\src\ZLib-build"

SET "PATH=%WIN_ROOT%;%WIN32_ROOT%;%WIN32_ROOT%\Wbem;%WIN32_ROOT%\WindowsPowerShell\v1.0;%WIN32_ROOT%\OpenSSH"
SET "PATH=%GIT_ROOT%\cmd;%CMAKE_ROOT%\bin;%PATH%"
SET "PYTHONPATH=%VIAME_INSTALL_DIR%\%PYTHON_SUBDIR%;%VIAME_INSTALL_DIR%\%PYTHON_SUBDIR%\site-packages"

REM -------------------------------------------------------------------------------------------------------
REM Perform Actual Build
REM -------------------------------------------------------------------------------------------------------

REM This build proceedure currently requires making TMP directories at C:\tmp to get around paths
REM which sometimes become too long for windows.

IF EXIST build rmdir /s /q build

IF NOT EXIST C:\tmp mkdir C:\tmp
IF EXIST C:\tmp\kv2 rmdir /s /q C:\tmp\kv2
IF EXIST C:\tmp\vm2 rmdir /s /q C:\tmp\vm2

git submodule update --init --recursive

REM If running locally instead of on Jenkins server, file jenkins_dashboard.cmake should be a renamed
REM version of the file located at jenkins/CTestBuildOnlyPipeline, with 'platform.cmake' in the
REM file pointed to build_server_windows_cpu.cmake (or alternatively the latter renamed to platform.cmake).

"%CMAKE_ROOT%\bin\ctest.exe" -S jenkins_dashboard.cmake -VV

REM -------------------------------------------------------------------------------------------------------
REM Final Install Generation Hacks Until Handled Better in VIAME CMake
REM -------------------------------------------------------------------------------------------------------

COPY "%WIN32_ROOT%\msvcr100.dll" %VIAME_INSTALL_DIR%\bin
COPY "%WIN32_ROOT%\vcruntime140_1.dll" %VIAME_INSTALL_DIR%\bin
COPY "%VDIST_ROOT%\vcomp140.dll" %VIAME_INSTALL_DIR%\bin
COPY "%WIN64_ROOT%\msvcr120.dll" %VIAME_INSTALL_DIR%\bin
COPY "%ZLIB_ROOT%\dll_x64\zlibwapi.dll" %VIAME_INSTALL_DIR%\bin
COPY "%ZLIB_BUILD_DIR%\Release\zlib1.dll" %VIAME_INSTALL_DIR%\bin

REM -------------------------------------------------------------------------------------------------------
REM Generate Final Zip File
REM -------------------------------------------------------------------------------------------------------

MOVE "%VIAME_INSTALL_DIR%" "%VIAME_BUILD_DIR%\VIAME"

"%ZIP_ROOT%\7z.exe" a "%VIAME_BUILD_DIR%\%OUTPUT_FILE%" "%VIAME_BUILD_DIR%\VIAME

MOVE "%VIAME_BUILD_DIR%\VIAME" "%VIAME_INSTALL_DIR%"
