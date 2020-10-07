rm -rf lambda-build
mkdir lambda-build
cp lambda_function.py main.py notify.py credentials.yml lambda-build
cd lambda-build
pip install -r ../requirements.txt -t ./
echo Please zip up the 'lambda-build' folder and upload it to AWS Lambda.
