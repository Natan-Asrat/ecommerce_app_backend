pip install -r requirements.txt
echo 'migrating'
python3.9 manage.py flush
python3.9 manage.py loaddata output.json
# python3.9 manage.py makemigrations
# python3.9 manage.py migrate