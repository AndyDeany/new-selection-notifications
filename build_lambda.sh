mkdir lambda-build
cp lambda_function.py main.py notify.py credentials.yml lambda-build
cd lambda-build
pip install -r ../requirements.txt -t ./
zip -r ../lambda-build.zip