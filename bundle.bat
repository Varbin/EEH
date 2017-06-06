@echo off
SET BACK=%cd%
cd %~dp0

mkdir _build
mkdir _build\temp

cd _build
copy ..\src\EEH.py temp\__main__.py
xcopy /s ..\src\EEHlib temp\EEHlib\
xcopy /s ..\_vendor temp\
del /s /Q temp\EEHlib\_vendor
del /S *.pyc
del /S *.pyo

cd temp
py -3 -m zipfile -c ..\temp.zip .
cd ..

py -3 -m zipapp temp.zip -o EEH.pyz -p "/usr/bin/env python3"

del temp.zip
cd ..

rmdir /S /Q _build\temp

cd %BACK%
SET BUILD=%RANDOM%
mkdir dist
cp _build\EEH.pyz dist\EEH-%BUILD%.pyz
echo Build %BUILD% finished!

