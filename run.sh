if [! -d "venv"]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install -r requirements.txt
python3 manage.py makemigrations
python3 manage.py migrate
python3 manage.py loaddata category_data.json
python3 manage.py createsuperuser
python3 manage.py runserver 0.0.0.0:8000