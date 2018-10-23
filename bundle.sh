#@echo off
#SET BACK=%cd%
#cd %~dp0

mkdir _build
mkdir _build/temp

cd _build
cp ../src/EEH.py temp/__main__.py
cp -r ../src/EEHlib/ temp/EEHlib/
cp -r ../_vendor/* temp
#del /s /Q temp/EEHlib/_vendor
#del /S *.pyc
#del /S *.pyo

cd temp
python3 -m zipfile -c ../temp.zip .
cd ..

python3 -m zipapp temp.zip -o EEH.pyz -p "/usr/bin/env python3"

rm temp.zip
cd ..
#/etc/systemd/system/EEH.service
#rm -r _build/temp

#cd %BACK%
#SET BUILD=%RANDOM%
#mkdir dist
#cp _build\EEH.pyz dist\EEH-%BUILD%.pyz
#echo Build %BUILD% finished!

