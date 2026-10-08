@echo off
REM ====================================================================
REM CourtVision Windows Production Build Script
REM Compiles CourtVision into a standalone Windows executable and release package.
REM ====================================================================

echo [CourtVision Build] Starting Windows application build process...

REM 1. Clean previous build artifacts
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist release rmdir /s /q release

REM 2. Run PyInstaller build
echo [CourtVision Build] Compiling executable via PyInstaller...
py -m PyInstaller courtvision.spec --noconfirm

if %ERRORLEVEL% NEQ 0 (
    echo [CourtVision Build] ERROR: PyInstaller compilation failed!
    exit /b %ERRORLEVEL%
)

REM 3. Prepare standalone production release folder
echo [CourtVision Build] Assembling release package...
mkdir release\CourtVision
xcopy /E /I /Y dist\CourtVision release\CourtVision

REM 4. Ensure writable runtime directories exist in release package
if not exist release\CourtVision\config mkdir release\CourtVision\config
if not exist release\CourtVision\ads mkdir release\CourtVision\ads
if not exist release\CourtVision\models mkdir release\CourtVision\models
if not exist release\CourtVision\output mkdir release\CourtVision\output
if not exist release\CourtVision\logs mkdir release\CourtVision\logs

REM Copy default configuration & model files if not already present
if exist models\yolov8n-seg.pt copy /Y models\yolov8n-seg.pt release\CourtVision\models\
if exist config\court.json copy /Y config\court.json release\CourtVision\config\
if exist config\ads.json copy /Y config\ads.json release\CourtVision\config\
if exist config\cameras.json copy /Y config\cameras.json release\CourtVision\config\
if exist ads\* copy /Y ads\* release\CourtVision\ads\
if exist input\* xcopy /E /I /Y input release\CourtVision\input\
if exist README.md copy /Y README.md release\CourtVision\README.txt

echo ====================================================================
echo [CourtVision Build] SUCCESS: Standalone Windows release generated!
echo Executable: release\CourtVision\CourtVision.exe
echo ====================================================================
