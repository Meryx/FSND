#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
import sys
from flask import Flask, render_template, request, Response, flash, redirect, url_for, abort
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func, case
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)
logging.basicConfig(level=logging.DEBUG)

# TODO: connect to a local postgresql database

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#



artist_genre = db.Table('artist_genre',
  db.Column('artist_id', db.Integer, db.ForeignKey('Artist.id'), primary_key=True),
  db.Column('genre_id', db.Integer, db.ForeignKey('Genre.id'), primary_key=True)
)

venue_genre = db.Table('venue_genre',
  db.Column('venue_id', db.Integer, db.ForeignKey('Venue.id'), primary_key=True),
  db.Column('genre_id', db.Integer, db.ForeignKey('Genre.id'), primary_key=True)
)

class Show(db.Model):
    __tablename__ = 'Show'
  
    id = db.Column('id', db.Integer, primary_key=True)
    venue_id = db.Column('venue_id', db.Integer, db.ForeignKey('Venue.id'))
    start_date = db.Column('date', db.DateTime(), nullable=False)
    artist_id = db.Column('artist_id', db.Integer, db.ForeignKey('Artist.id'))



class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120))
    website = db.Column(db.String(500))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean, nullable=False, default=False)
    seeking_description = db.Column(db.String(1000))
    genres = db.relationship('Genre', secondary=venue_genre, backref=db.backref('Venue', lazy=True))
    shows = db.relationship('Show', backref='Venue', lazy=True)


    # TODO: implement any missing fields, as a database migration using Flask-Migrate

class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120))
    website = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean, nullable=False, default=False)
    seeking_description = db.Column(db.String(1000))
    image_link = db.Column(db.String(500))
    genres = db.relationship('Genre', secondary=artist_genre, backref=db.backref('Artist', lazy=True))
    shows = db.relationship('Show', backref='Artist', lazy=True)


    

class Genre(db.Model):
  __tablename__ = 'Genre'

  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(), nullable=False)



#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # TODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  

  venue_data = []
  alt_data = []
  condition = case(
    [
      (Show.start_date >= func.now(), 1)
    ], else_ = None
  )

  list_states = db.session.query(Venue.state).distinct().order_by(Venue.state).all()
  for state in list_states:
    list_cities = db.session.query(Venue.city).distinct().filter(Venue.state == state.state).order_by(Venue.city).all()
    for city in list_cities:
      list_venues = db.session.query(Venue, func.count(condition)).join(Show, isouter=True).filter(Venue.city == city.city).group_by(Venue.id).order_by(func.count(condition)).all()
      for ven in list_venues:
        venue_data.append(
          {
            "id": ven.Venue.id,
            "name": ven.Venue.name,
            "num_upcoming_shows": ven[1],            
          }
        )
      alt_data.append(
        {
          "city": city.city,
          "state": state.state,
          "venues": venue_data
        }
      )
      venue_data = []


  return render_template('pages/venues.html', areas=alt_data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  

  condition = case(
    [
      (Show.start_date >= func.now(), 1)
    ], else_ = None
  )

  search = request.form['search_term']
  search_tag = "%{}%".format(search)
  query = db.session.query(Venue).filter(func.upper(Venue.name).like(func.upper(search_tag))).all()
  alt_response = []
  for result in query:
    alt_response.append(
      {
        "id": result.id,
        "name": result.name,
        "num_upcoming_shows": len(db.session.query(func.count(condition)).filter(result.id == Show.venue_id).group_by(Show.venue_id).all())
      }
    )
  final_response = {
    "count": len(query),
    "data": alt_response,
  }
  return render_template('pages/search_venues.html', results=final_response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  
  query = Venue.query.get(venue_id)
  upcoming_show_count = 0
  past_show_count = 0

  if query:
    past_shows = []
    upcoming_shows = []
    genres = []
    upcoming_show_query = db.session.query(Show).filter(Show.start_date >= func.now(), query.id == Show.venue_id).all()
    past_show_query = db.session.query(Show).filter(Show.start_date < func.now(), query.id == Show.venue_id).all()
    for show in upcoming_show_query:
      artist = Artist.query.get(show.artist_id)
      upcoming_shows.append(
        {
          "artist_id": artist.id,
          "artist_name": artist.name,
          "artist_image_link": 'https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80',
          "start_time": str(show.start_date),         
        }
      )
      upcoming_show_count = upcoming_show_count + 1
    for show in past_show_query:
      artist = Artist.query.get(show.artist_id)
      past_shows.append(
        {
          "artist_id": artist.id,
          "artist_name": artist.name,
          "artist_image_link": 'https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80',
          "start_time": str(show.start_date),
        }
      )
      past_show_count = past_show_count + 1
    for genre in query.genres:
      genres.append(genre.name)
    data = {
      "id": query.id,
      "name": query.name,
      "genres": genres,
      "address": query.address,
      "city": query.city, 
      "state": query.state,
      "phone": query.phone,
      "website": query.website,
      "facebook_link": query.facebook_link,
      "seeking_talent": query.seeking_talent,
      "image_link": 'https://images.unsplash.com/photo-1485686531765-ba63b07845a7?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=747&q=80',
      "past_shows": past_shows,
      "upcoming_shows": upcoming_shows,
      "past_shows_count": past_show_count,
      "upcoming_shows_count": upcoming_show_count,
    }
       
  else:
    abort(404)

  #data = list(filter(lambda d: d['id'] == venue_id, [data1, data2, data3]))[0]
  return render_template('pages/show_venue.html', venue=data)

  

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  error = False
  name = request.form['name']
  city = request.form['city']
  state = request.form['state']
  phone = request.form['phone']
  address = request.form['address']
  genres = request.form.getlist('genres')
  facebook_link = request.form['facebook_link']
  genre_list = []


  #If a selected genre is not in the database, add it
  #Otherwise just retrieve it and append it to the list
  for e in genres:
   temp = Genre(name=e)
   query = Genre.query.filter(Genre.name == e).first()
   if not query:
    db.session.add(temp)
    genre_list.append(temp)
   else:
    genre_list.append(query)


  venue = Venue(name = name, city = city, state = state, phone = phone, facebook_link = facebook_link, address = address)
  venue.genres = genre_list
  

  try:
    db.session.add(venue)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
  finally:
    db.session.close()

  if not error:
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  else:
    flash('An error occured. Venue ' + request.form['name'] + ' could not be listed.')

  
  return render_template('pages/home.html')
  




@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database

  artists = []
  query = db.session.query(Artist).order_by(Artist.name).all()
  for artist in query:
    artists.append(
      {
        "id": artist.id,
        "name": artist.name,
      }
    )
  return render_template('pages/artists.html', artists=artists)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  response={
    "count": 1,
    "data": [{
      "id": 4,
      "name": "Guns N Petals",
      "num_upcoming_shows": 0,
    }]
  }

  condition = case(
    [
      (Show.start_date >= func.now(), 1)
    ], else_ = None
  )

  search = request.form['search_term']
  search_tag = "%{}%".format(search)
  query = db.session.query(Artist).filter(func.upper(Artist.name).like(func.upper(search_tag))).all()
  alt_response = []
  for result in query:
    alt_response.append(
      {
        "id": result.id,
        "name": result.name,
        "num_upcoming_shows": len(db.session.query(func.count(condition)).filter(result.id == Show.artist_id).group_by(Show.artist_id).all())
      }
    )
  final_response = {
    "count": len(query),
    "data": alt_response,
  }
  return render_template('pages/search_artists.html', results=final_response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  data1={
    "id": 4,
    "name": "Guns N Petals",
    "genres": ["Rock n Roll"],
    "city": "San Francisco",
    "state": "CA",
    "phone": "326-123-5000",
    "website": "https://www.gunsnpetalsband.com",
    "facebook_link": "https://www.facebook.com/GunsNPetals",
    "seeking_venue": True,
    "seeking_description": "Looking for shows to perform at in the San Francisco Bay Area!",
    "image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80",
    "past_shows": [{
      "venue_id": 1,
      "venue_name": "The Musical Hop",
      "venue_image_link": "https://images.unsplash.com/photo-1543900694-133f37abaaa5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=400&q=60",
      "start_time": "2019-05-21T21:30:00.000Z"
    }],
    "upcoming_shows": [],
    "past_shows_count": 1,
    "upcoming_shows_count": 0,
  }
  data2={
    "id": 5,
    "name": "Matt Quevedo",
    "genres": ["Jazz"],
    "city": "New York",
    "state": "NY",
    "phone": "300-400-5000",
    "facebook_link": "https://www.facebook.com/mattquevedo923251523",
    "seeking_venue": False,
    "image_link": "https://images.unsplash.com/photo-1495223153807-b916f75de8c5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=334&q=80",
    "past_shows": [{
      "venue_id": 3,
      "venue_name": "Park Square Live Music & Coffee",
      "venue_image_link": "https://images.unsplash.com/photo-1485686531765-ba63b07845a7?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=747&q=80",
      "start_time": "2019-06-15T23:00:00.000Z"
    }],
    "upcoming_shows": [],
    "past_shows_count": 1,
    "upcoming_shows_count": 0,
  }
  data3={
    "id": 6,
    "name": "The Wild Sax Band",
    "genres": ["Jazz", "Classical"],
    "city": "San Francisco",
    "state": "CA",
    "phone": "432-325-5432",
    "seeking_venue": False,
    "image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
    "past_shows": [],
    "upcoming_shows": [{
      "venue_id": 3,
      "venue_name": "Park Square Live Music & Coffee",
      "venue_image_link": "https://images.unsplash.com/photo-1485686531765-ba63b07845a7?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=747&q=80",
      "start_time": "2035-04-01T20:00:00.000Z"
    }, {
      "venue_id": 3,
      "venue_name": "Park Square Live Music & Coffee",
      "venue_image_link": "https://images.unsplash.com/photo-1485686531765-ba63b07845a7?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=747&q=80",
      "start_time": "2035-04-08T20:00:00.000Z"
    }, {
      "venue_id": 3,
      "venue_name": "Park Square Live Music & Coffee",
      "venue_image_link": "https://images.unsplash.com/photo-1485686531765-ba63b07845a7?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=747&q=80",
      "start_time": "2035-04-15T20:00:00.000Z"
    }],
    "past_shows_count": 0,
    "upcoming_shows_count": 3,
  }

  upcoming_show_count = 0
  past_show_count = 0

  query = Artist.query.get(artist_id)
  if query:
    past_shows = []
    upcoming_shows = []
    genres = []
    upcoming_show_query = db.session.query(Show).filter(Show.start_date >= func.now(), query.id == Show.venue_id).all()
    past_show_query = db.session.query(Show).filter(Show.start_date < func.now(), query.id == Show.venue_id).all()
    for show in upcoming_show_query:
      venue = Venue.query.get(show.venue_id)
      upcoming_shows.append(
        {
          "venue_id": venue.id,
          "venue_name": venue.name,
          "venue_image_link": 'https://images.unsplash.com/photo-1485686531765-ba63b07845a7?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=747&q=80',
          "start_time": str(show.start_date),         
        }
      )
      upcoming_show_count = upcoming_show_count + 1
    for show in past_show_query:
      venue = Venue.query.get(show.venue_id)
      past_shows.append(
        {
          "venue_id": venue.id,
          "venue_name": venue.name,
          "venue_image_link": 'https://images.unsplash.com/photo-1485686531765-ba63b07845a7?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=747&q=80',
          "start_time": str(show.start_date),         
        }
      )
      past_show_count = past_show_count + 1
    for genre in query.genres:
      genres.append(genre.name)

  else:
    abort(404)

  data={
    "id": query.id,
    "name": query.name,
    "genres": genres,
    "city": query.city,
    "state": query.state,
    "phone": query.phone,
    "seeking_venue": query.seeking_venue,
    "image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": past_show_count,
    "upcoming_shows_count": upcoming_show_count,
  }

  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist={
    "id": 4,
    "name": "Guns N Petals",
    "genres": ["Rock n Roll"],
    "city": "San Francisco",
    "state": "CA",
    "phone": "326-123-5000",
    "website": "https://www.gunsnpetalsband.com",
    "facebook_link": "https://www.facebook.com/GunsNPetals",
    "seeking_venue": True,
    "seeking_description": "Looking for shows to perform at in the San Francisco Bay Area!",
    "image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80"
  }
  
  # TODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue={
    "id": 1,
    "name": "The Musical Hop",
    "genres": ["Jazz", "Reggae", "Swing", "Classical", "Folk"],
    "address": "1015 Folsom Street",
    "city": "San Francisco",
    "state": "CA",
    "phone": "123-123-1234",
    "website": "https://www.themusicalhop.com",
    "facebook_link": "https://www.facebook.com/TheMusicalHop",
    "seeking_talent": True,
    "seeking_description": "We are on the lookout for a local artist to play every two weeks. Please call us.",
    "image_link": "https://images.unsplash.com/photo-1543900694-133f37abaaa5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=400&q=60"
  }
  # TODO: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  error = False
  name = request.form['name']
  city = request.form['city']
  state = request.form['state']
  phone = request.form['phone']
  genres = request.form.getlist('genres')
  facebook_link = request.form['facebook_link']
  genre_list = []


  #If a selected genre is not in the database, add it
  #Otherwise just retrieve it and append it to the list
  for e in genres:
   temp = Genre(name=e)
   query = Genre.query.filter(Genre.name == e).first()
   if not query:
    db.session.add(temp)
    genre_list.append(temp)
   else:
    genre_list.append(query)



  artist = Artist(name = name, city = city, state = state, phone = phone, facebook_link = facebook_link)
  artist.genres = genre_list
  
 
  try:
    db.session.add(artist)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
  finally:
    db.session.close()

  if not error:
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  else:
    flash('An error occured. Artist ' + request.form['name'] + ' could not be listed.')

  
  return render_template('pages/home.html')
  
  # on successful db insert, flash success
  
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
  


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  
  data = []
  query = db.session.query(Show).all()
  for show in query:
    data.append(
      {
        "venue_id": show.venue_id,
        "venue_name": Venue.query.get(show.venue_id).name,
        "artist_id": show.artist_id,
        "artist_name": Artist.query.get(show.artist_id).name,
        "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
        "start_time": str(show.start_date),
      }
    )
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead
  error = False
  artist_id = request.form['artist_id']
  venue_id = request.form['venue_id']
  timeDate = request.form['start_time']
  
  show = Show(artist_id = artist_id, venue_id = venue_id, start_date = timeDate)

  try:
    db.session.add(show)
    db.session.commit()
  except:
    db.session.rollback()
  finally:
    db.session.close()
  if not error:
      flash('Show was successfully listed!')
  else:
      flash('An error occured. Show could not be listed.')
  
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
