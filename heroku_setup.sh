#!/bin/bash

# This is to give an idea of how to set Heroku up for this application.

heroku create publicsciencehive
heroku addons:add mongohq

heroku config:add HEROKU='true'
heroku config:add SECRET_KEY='some-secret-key'
heroku config:add AUTH_USER='pubsci'
heroku config:add AUTH_PASS='some-password'
heroku config:add MAIL_USER='someemail@email.com'
heroku config:add MAIL_PASS='some-password'
heroku config:add GOOGLE_CLIENT_ID='some-google-client-id'
heroku config:add GOOGLE_CLIENT_SECRET='some-google-client-secret'
heroku config:add GITHUB_CLIENT_ID='some-github-client-id'
heroku config:add GITHUB_CLIENT_SECRET='some-github-client-secret'

git push heroku master

# Use this to check on the status.
heroku ps

heroku domains:add hive.publicscience.co
