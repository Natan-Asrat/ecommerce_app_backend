pip install -r requirements.txt
echo 'migrating'
python3.9 manage.py loaddata data.json
# python3.9 manage.py makemigrations
# python3.9 manage.py migrate