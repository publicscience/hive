Public Science Hive
====================

## Setup
It's recommended that you use a virtualenv:
```
$ virtualenv-2.7 ~/envs/hive --no-site-packages
$ source ~/envs/hive/bin/activate
```

Run [MongoDB](http://www.mongodb.org/downloads):
```
$ mongod
```

Clone repo and then install dependencies:
```
$ git clone https://github.com/publicscience/hive.git
$ cd hive
$ pip install -r requirements.txt
```

Setup Flask configuration:
```
$ mv config-sample.py config.py
$ vi config.py
```

Run the Flask application:
```
$ python application.py
```

Check out the site at `localhost:5000` (by default).



Dev Notes
=========

```
/flask_mongoengine/wtf/orm.py
line 225 has a Python 3 incompatibility.
It uses iteritems(), it should be items().
```