import os
from flask import Flask, render_template, session, redirect, url_for, flash, request
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField, ValidationError
from wtforms.validators import Required, Length
from flask_sqlalchemy import SQLAlchemy
from flask_script import Manager, Shell 
from flask_migrate import Migrate, MigrateCommand
import requests
import json
import twitter_info
import tweepy

import sys
def uprint(*objects, sep=' ', end='\n', file=sys.stdout):
    enc = file.encoding
    if enc == 'UTF-8':
        print(*objects, sep=sep, end=end, file=file)
    else:
        f = lambda obj: str(obj).encode(enc, errors='backslashreplace').decode(enc)
        print(*map(f, objects), sep=sep, end=end, file=file)

def get_nyt_review(movie_name):
	api_key = '98eba02323d11b2615cb90216f95dc76:12:74970859'
	uprint(movie_name)
	movie_name = movie_name.replace(' ','+')
	uprint(movie_name)
	movie_name = "'"+movie_name+"'"
	url = 'http://api.nytimes.com/svc/movies/v2/reviews/search.json?query={}&api-key={}'.format(movie_name,api_key)
	data = requests.get(url)
	json_data = json.loads(data.text)
	review_dict = {}
	for result in json_data['results']:
		movie_name = movie_name.replace("'",'')
		review_dict[movie_name.replace('+',' ')] = {'review':result['summary_short'],'link':result['link']['url'],'headline':result['headline']}
	return review_dict

uprint(get_nyt_review('Mad Max: Fury Road'))
