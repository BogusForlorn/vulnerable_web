This is the sample web application that is vulnerable to SQLi and XSS. This is to test PenAI.py
```
pip install gunicorn flask --break-system-packages #remove --break-system-packages if you don't need it
python setup.py #setup the db

#use gunicorn to run the server
gunicorn -w 4 -b 0.0.0.0:5000 vuln_app:app
```
To reset the DB after hammering it with PenAI.py, do 
```
python reset.py #cleans up the db
#then rerun the server with gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 vuln_app:app
```
