#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
import datetime
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'Venue'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean)
    seeking_description = db.Column(db.String(600))
    genres = db.Column(db.String())
    shows = db.relationship('Show', backref='Venue', lazy=True)
  
    def as_dict(self):
      return{
            'id' :self.id,
            'name' :self.name,
            'genres' : self.genres,
            'state': self.state,
            'address' :self.address,
            'city' :self.city,
            'phone' :self.phone,
            'website' :self.website,
            'facebook_link':self.facebook_link,
            'seeking_talent' :self.seeking_talent,
            'seeking_description' :self.seeking_description,
            'image_link' :self.image_link
        }

class Artist(db.Model):
    __tablename__ = 'Artist'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String())
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean)
    seeking_description = db.Column(db.String(600))
    website = db.Column(db.String(120))
    shows = db.relationship('Show', backref='Artist', lazy=True,)\
    
    def as_dict(self):
      return {
            'id' :self.id,
            'name': self.name,
            'city': self.city,
            'state': self.state,
            'phone': self.phone,
            'genres': self.genres,
            'image_link': self.image_link,
            'facebook_link': self.facebook_link,
            'seeking_venue': self.seeking_venue,
            'seeking_description': self.seeking_description,
            'website': self.website
            }

class Show(db.Model):
    __tablename__ = 'Show'
    id = db.Column(db.Integer, primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'), nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    
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
  data=[]
  for venues in Venue.query.distinct(Venue.city, Venue.state):
    venues_per_city = []  
    for venue in  Venue.query.filter_by(city=venues.city, state=venues.state):
      venues_per_city.append(
        {"id": venue.id,
        "name": venue.name,
        "num_upcoming_shows": 0
        }
      )
    data.append({
      "city": venues.city,
      "state": venues.state,
      "venues": venues_per_city
    })
  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  search_term = request.form.get('search_term', '')
  venues = Venue.query.filter(Artist.name.ilike('%'+search_term+'%')).all()
  response={
    "count": len(venues),
    "data": venues
  }
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  venue_query = Venue.query.filter_by(id=venue_id)
  current_time = datetime.datetime.utcnow()
  shows = db.session.query(Show).filter_by(venue_id=venue_id).all()
  upcoming_shows =  [{
                  "artist_id": show.artist_id,
                  "artist_name": show.Artist.name,
                  "artist_image_link": show.Artist.image_link,
                  "start_time": show.start_time.strftime("%m/%d/%Y, %H:%M")
  } for show in shows if show.start_time > current_time]
  past_shows =  [{
                  "artist_id": show.artist_id,
                  "artist_name": show.Artist.name,
                  "artist_image_link": show.Artist.image_link,
                  "start_time": show.start_time.strftime("%m/%d/%Y, %H:%M")
  } for show in shows if show.start_time < current_time]
  venue = venue_query.first().as_dict()
  venue['past_shows'] = past_shows
  venue['upcoming_shows'] = upcoming_shows
  venue["past_shows_count"] = len(past_shows)
  venue["upcoming_shows_count"] = len(upcoming_shows)
  return render_template('pages/show_venue.html', venue=venue)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  try:
    if ('seeking_talent' in request.form) and \
    ('seeking_description' in request.form):
      seeking_talent = request.form['seeking_talent'] == 'y'
      seeking_description = request.form['seeking_description']
    else:
      seeking_talent = False
      seeking_description = ""
    venue = Venue(
      name=request.form['name'],
      genres= request.form.getlist('genres'),
      city=request.form['city'],
      state= request.form['state'],
      phone=request.form['phone'],
      website=request.form['website'],
      address = request.form['address'],
      image_link=request.form['image_link'],
      facebook_link=request.form['facebook_link'],
      seeking_talent=seeking_talent,
      seeking_description=seeking_description
    )
    db.session.add(venue)
    db.session.commit()
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  except:
    db.session.rollback()
    flash('Venue ' + request.form['name'] + 'could not be listed!')
  finally:
    db.session.close()
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
  data = []
  for artist in Artist.query.all():
    data.append(
      {"id": artist.id, "name":artist.name}
    )
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  search_term = request.form.get('search_term', '')
  artists = Artist.query.filter(Artist.name.ilike('%'+search_term+'%')).all()
  response={
    "count": len(artists),
    "data": artists
  }
  return render_template('pages/search_artists.html', results=response, search_term=search_term)

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  artist_query = Artist.query.filter_by(id=artist_id)
  current_time = datetime.datetime.utcnow()
  shows = db.session.query(Show).filter_by(artist_id=artist_id).all()
  upcoming_shows =  [{
                  "venue_id": show.venue_id,
                  "venue_name": show.Venue.name,
                  "venue_image_link": show.Venue.image_link,
                  "start_time": show.start_time.strftime("%m/%d/%Y, %H:%M")
  } for show in shows if show.start_time > current_time]
  past_shows =  [{
                  "venue_id": show.venue_id,
                  "venue_name": show.Venue.name,
                  "venue_image_link": show.Venue.image_link,  
                  "start_time": show.start_time.strftime("%m/%d/%Y, %H:%M")
  } for show in shows if show.start_time < current_time]
  _artist = artist_query.first()
  artist = _artist.as_dict()
  artist['genres'] =  _artist.genres.replace('{','').replace('}','').split(',')
  artist["past_shows"] = past_shows
  artist["upcoming_shows"] = upcoming_shows
  artist["past_shows_count"] = len(past_shows)
  artist["upcoming_shows_count"] = len(upcoming_shows)
  return render_template('pages/show_artist.html', artist=artist)

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
  try:
    if ('seeking_venue' in request.form) and \
    ('seeking_description' in request.form):
      seeking_venue = request.form['seeking_venue'] == 'y'
      seeking_description = request.form['seeking_description']
    else:
      seeking_venue = False
      seeking_description = ""
    artist = Artist(
      name=request.form['name'],
      genres= request.form.getlist('genres'),
      city=request.form['city'],
      state= request.form['state'],
      phone=request.form['phone'],
      website=request.form['website'],
      image_link=request.form['image_link'],
      facebook_link=request.form['facebook_link'],
      seeking_venue=seeking_venue,
      seeking_description=seeking_description
    )
    db.session.add(artist)
    db.session.commit()
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  except:
    db.session.rollback()
    flash('Artist ' + request.form['name'] + 'could not be listed!')
  finally:
    db.session.close()
  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  shows = []
  for show in Show.query.all():
    show_details = {
      "venue_id": show.Venue.id,
      "venue_name": show.Venue.name,
      "artist_id": show.Artist.id,
      "artist_name": show.Artist.name,
      "artist_image_link": show.Artist.image_link,
      "start_time": str(show.start_time)
    }
    shows.append(show_details)
  return render_template('pages/shows.html', shows=shows)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  try:
    artist_id = request.form['artist_id']
    venue_id = request.form['venue_id']
    if Artist.query.filter_by(id=artist_id) and \
      Venue.query.filter_by(id=venue_id):
        show = Show(artist_id= artist_id,
        venue_id=venue_id,
        start_time= request.form['start_time']
      )
        db.session.add(show)
        db.session.commit()
        flash('Show was successfully listed!')
    else:
      flash('Show or Artist invalid!')
      raise Exception
  except:
    flash('Show could not be listed!')
    db.session.rollback()
  finally:
    db.session.close()
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
