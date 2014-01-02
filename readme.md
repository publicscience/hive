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

## Testing

To run tests, do:
```
$ ./test
```
This sets the `HIVE_TESTING` env var up so the test database is used.

## Deploying to Heroku
The app is setup to be deployed to [Heroku](https://heroku.com).

You can use `heroku_setup.sh` as guidance for the terminal commands
needed to set it up.
The key here is that you need to setup Heroku environment variables for
all sensitive configuration options. The application will check for a
`HEROKU` environment variable, and if it is set, it will load the Heroku
configuration, which is set to automatically load these sensitive values
from env vars.