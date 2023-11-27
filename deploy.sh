pip install -r requirements.txt
echo 'migrating'
python3.9 manage.py flush --noinput
python3.9 manage.py loaddata output.json --noinput
# python3.9 manage.py makemigrations
# python3.9 manage.py migrate