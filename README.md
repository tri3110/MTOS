"# MTB_SYSTEM" 

# python -m venv venv
# venv/scripts/activate
# pip install -r .\requirements.txt
pip install Pillow
CREATE EXTENSION IF NOT EXISTS pg_trgm;
python manage.py makemigrations
python manage.py migrate
python manage.py runserver

git remote add origin https://github.com/tri3110/MTOS.git