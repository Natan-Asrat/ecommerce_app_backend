if not exist "venv" (python -m venv venv)
call venv/Scripts/activate
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py loaddata category_data.json
python manage.py loaddata user_data.json
python manage.py loaddata post_data.json
python manage.py loaddata post_image_data.json
python manage.py loaddata packages_data.json
python manage.py runserver 0.0.0.0:8000
