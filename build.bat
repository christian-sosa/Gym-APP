@echo off
REM ============================================
REM BloomFitness - Script de Build para Windows
REM ============================================

echo.
echo ========================================
echo   BloomFitness - Generando Ejecutable
echo ========================================
echo.

REM Verificar Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python no esta instalado o no esta en el PATH
    pause
    exit /b 1
)

REM Verificar entorno virtual
if exist "venv\Scripts\activate.bat" (
    echo Activando entorno virtual...
    call venv\Scripts\activate.bat
) else (
    echo NOTA: No se encontro entorno virtual. Usando Python del sistema.
)

REM Instalar dependencias si es necesario
echo.
echo Verificando dependencias...
pip install -r requirements.txt -q

REM Verificar PyInstaller
pyinstaller --version >nul 2>&1
if errorlevel 1 (
    echo Instalando PyInstaller...
    pip install pyinstaller
)

REM Limpiar builds anteriores
echo.
echo Limpiando builds anteriores...
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist

REM Generar ejecutable
echo.
echo Generando ejecutable...
pyinstaller BloomFitness.spec

REM Verificar resultado
if exist "dist\BloomFitness.exe" (
    echo.
    echo ========================================
    echo   BUILD EXITOSO!
    echo ========================================
    echo.
    echo El ejecutable se encuentra en:
    echo   dist\BloomFitness.exe
    echo.
    
    REM Copiar base de datos vacía si existe
    if not exist "dist\data" mkdir dist\data
    
    echo Listo para distribuir.
) else (
    echo.
    echo ERROR: No se pudo generar el ejecutable.
    echo Revise los mensajes de error anteriores.
)

echo.
pause
