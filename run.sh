git pull
rm -rf venv/
python -m venv venv
source venv/Scripts/activate
pip install -r requirements.txt
echo Running notifications script...
python main.py
