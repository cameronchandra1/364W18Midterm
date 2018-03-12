###############################
####### SETUP (OVERALL) #######
###############################

# Import statements
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

basedir = os.path.abspath(os.path.dirname(__file__))
## App setup code
app = Flask(__name__)
app.debug = True
app.use_reloader = True

## All app.config values
app.config['SECRET_KEY'] = 'hardtoguessstring'
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://postgres:29Malysana@localhost:5432/364Midtermdb" 
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

## Statements for db setup (and manager setup if using Manager)
manager = Manager(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
manager.add_command('db', MigrateCommand)


######################################
######## HELPER FXNS (If any) ########
######################################

# this helper function access the OMDB API and retrieves the plot of the user's movie
def get_movie_plot(movie_name):
	movie_name = movie_name.replace(' ', '+')
	api_key = '9f0092a6'
	url = 'http://www.omdbapi.com/?apikey={}&t={}&type=movie&plot=short&r=json'.format(api_key,movie_name)
	data = requests.get(url)
	json_data = json.loads(data.text)
	return json_data['Plot']
# this helper function takes in a movie name, access the twitter api, and returns tweets regarding the movie name
def get_tweets(movie_name): 
	consumer_key = twitter_info.consumer_key
	consumer_secret = twitter_info.consumer_secret
	access_token = twitter_info.access_token
	access_token_secret = twitter_info.access_token_secret
	auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
	auth.set_access_token(access_token, access_token_secret)
	api = tweepy.API(auth, parser=tweepy.parsers.JSONParser()) 
	movie_name = movie_name.replace(' ','')
	hashtag = '#'+movie_name
	results = api.search(q=hashtag,count=3)
	return results['statuses']

# this helper function gets review information from the NYT API
def get_nyt_review(movie_name):
	api_key = '98eba02323d11b2615cb90216f95dc76:12:74970859'
	movie_name = movie_name.replace(' ','+')
	movie_name = "'"+movie_name+"'"
	url = 'http://api.nytimes.com/svc/movies/v2/reviews/search.json?query={}&api-key={}'.format(movie_name,api_key)
	data = requests.get(url)
	json_data = json.loads(data.text)
	review_dict = {}
	for result in json_data['results']:
		movie_name = movie_name.replace("'",'')
		review_dict[movie_name.replace('+',' ')] = {'review':result['summary_short'],'link':result['link']['url'],'headline':result['headline']}
	return review_dict


##################
##### MODELS #####
##################

# Table that lists all the movies 
class Movies(db.Model):
	__tablename__ = "movies"
	id = db.Column(db.Integer,primary_key=True)
	movie_name = db.Column(db.String(64), unique=True)
	overview = db.Column(db.String(500))

	def __repr__(self):
		return "{}: {}".format(self.movie_name,self.overview,self.id)


# Table that lists inputted movies and associated tweets 
class Tweets(db.Model):
	__tablename__ = 'tweets'
	id = db.Column(db.Integer,primary_key=True)
	tweet = db.Column(db.String(500))
	movie_name = db.Column(db.String(64),db.ForeignKey('movies.movie_name'))
	movies = db.relationship('Movies',backref='Tweets')

	def __repr__(self):
		return "{} - Tweet: {} (ID: {})".format(self.movie_name,self.tweet,self.id)


# Table that lists movie reviews and information
class NYT(db.Model):
	__tablename__ = 'nytimes'
	id = db.Column(db.Integer,primary_key=True,unique=True)
	movie_name = db.Column(db.String(64),db.ForeignKey('movies.movie_name'))
	movies = db.relationship('Movies',backref='NYT')
	review = db.Column(db.String(500))
	link = db.Column(db.String(255))
	headline = db.Column(db.String(255))

	def __repr__(self):
		return "Movie: {} - Review: {}  (ID: {})".format(self.movie_name,self.review)


###################
###### FORMS ######
###################

# Form to appear on homepage
class MovieForm(FlaskForm):
    movies = StringField("Please enter your favorite movies (seperate each with a comma):",validators=[Required()]) 
    submit = SubmitField()

# Form to appear on tweets page + custom validator
class TweetForm(FlaskForm):
	movies = StringField("Enter saved movie names to see tweets about them (seperate with commas): ",validators=[Required()])
	submit = SubmitField()

	def validate_movies(self,field):
		for movie in field.data.split(','):
			m = db.session.query(Movies).filter_by(movie_name=movie.strip()).first()
			if not m:
				raise ValidationError('This movie(s) has not been saved. Go to the Home Page and enter the movie name.')


		

####### Error Handlers ###### 
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

#######################
###### VIEW FXNS ######
#######################

# view for homepage, this function also includes all of the databasing
@app.route('/',methods=['GET','POST'])
def home():
    form = MovieForm() 
    if form.validate_on_submit():
    	movie_str = form.movies.data
    	movie_lst = movie_str.split(',')
    	for movie in movie_lst:
    		movie = movie.strip()
    		m = db.session.query(Movies).filter_by(movie_name=movie).first()
    		if m:
    			return redirect(url_for('all_movies'))
    		overview = get_movie_plot(movie)
    		new_movie = Movies(movie_name=movie,overview=overview)
    		db.session.add(new_movie)
    		db.session.commit()
    	for movie in movie_lst:
    		twitter_info = get_tweets(movie)
    		for tw in twitter_info:
    			tweet = tw['text']
    			tweet = tweet.strip()
    			t = Tweets(tweet=tweet,movie_name=movie.strip())
    			db.session.add(t)
    			db.session.commit()
    	for movie in movie_lst:
    		movie = movie.strip()
    		r = db.session.query(NYT).filter_by(movie_name=movie).first()
    		if r:
    			return redirect(url_for('all_movies'))
    		review_info = get_nyt_review(movie)
    		review = NYT(movie_name=movie,review=review_info[movie]['review'],link=review_info[movie]['link'],headline=review_info[movie]['headline'])
    		db.session.add(review)
    		db.session.commit() 
    	return redirect(url_for('all_movies'))
    return render_template('base.html',form=form)

# view to see all the movies and their descriptions
@app.route('/movies')
def all_movies():
    movies = Movies.query.all()
    return render_template('movies.html',movies=movies)

# This view has a form, and displays the data on the same page using POST
@app.route('/tweets',methods=['GET','POST'])
def find_tweets():
	form = TweetForm()
	movie_dict = {} 
	if form.validate_on_submit():
		movie_str = form.movies.data
		movie_lst = movie_str.split(',')
		for movie in movie_lst:
			tweets = db.session.query(Tweets.tweet).filter_by(movie_name=movie.strip()).all()
			movie_dict[movie] = tweets
	return render_template('tweet_form.html',form=form,movie_dict=movie_dict)

# view that displays all the saved movies NYT reviews
@app.route('/reviews')
def see_reviews():
	reviews = NYT.query.all()
	return render_template('nyt.html',reviews=reviews)









## Code to run the application...
if __name__ == '__main__':
				db.create_all() 
				app.run(use_reloader=True,debug=True) 



