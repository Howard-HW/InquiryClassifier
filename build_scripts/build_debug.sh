#!/bin/bash

echo "Creating build directory..."
mkdir -p build
cd build

echo "Creating virtual environment with Python 3.11..."
python3.11 -m venv venv
source venv/bin/activate

echo "Installing requirements..."
pip install --upgrade pip
pip install -r ../requirements.txt
pip install pyinstaller

echo "Building executable..."
pyinstaller --name="InquiryClassifier" \
            --onefile \
            --windowed \
            --add-data="../src/resources:resources" \
            --hidden-import=sklearn \
            --hidden-import=pandas \
            --hidden-import=numpy \
            --hidden-import=joblib \
            --hidden-import=openpyxl \
            --paths="../src" \
            --distpath="../dist" \
            --workpath="./temp" \
            --specpath="." \
            ../src/main.py

cd ..