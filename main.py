from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField
from wtforms.validators import DataRequired
import requests
import os

TMDB_SEARCH_URL = "https://api.themoviedb.org/3/search/movie"
MOVIE_INFO_URL = "https://api.themoviedb.org/3/movie"
TMDB_API = os.environ["TMDB_API"]

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///movies.db"
Bootstrap(app)
db = SQLAlchemy(app)

with app.app_context():
    class Movie(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        title = db.Column(db.String, unique=True, nullable=False)
        year = db.Column(db.Integer, nullable=False)
        description = db.Column(db.String, unique=True, nullable=False)
        rating = db.Column(db.Float, nullable=True)
        ranking = db.Column(db.Integer, nullable=True)
        review = db.Column(db.String, nullable=True)
        img_url = db.Column(db.String, unique=True, nullable=False)
    db.create_all()


    class RateMovieForm(FlaskForm):
        rating = FloatField("Rating", validators=[DataRequired()])
        review = StringField("Review")
        submit = SubmitField("Done")


    class AddMovieForm(FlaskForm):
        title = StringField("Movie title", validators=[DataRequired()])
        submit = SubmitField("Add movie")


    @app.route("/")
    def home():
        all_movies = Movie.query.order_by(Movie.rating).all()
        for i in range(len(all_movies)):
            all_movies[i].ranking = len(all_movies) - i
        db.session.commit()
        print(TMDB_API)
        return render_template("index.html", movies=all_movies)


    @app.route("/edit", methods=["GET", "POST"])
    def rate_movie():
        form = RateMovieForm()
        movie_id = request.args.get("id")
        selected_movie = Movie.query.get(movie_id)
        if form.validate_on_submit():
            selected_movie.rating = request.form["rating"]
            selected_movie.review = request.form["review"]
            db.session.commit()
            return redirect(url_for("home"))
        return render_template("edit.html", movie=selected_movie, form=form)


    @app.route("/delete")
    def delete():
        movie_id = request.args.get("id")
        selected_movie = Movie.query.get(movie_id)
        db.session.delete(selected_movie)
        db.session.commit()
        return redirect(url_for("home"))


    @app.route("/add", methods=["GET", "POST"])
    def add_movie():
        form = AddMovieForm()
        if form.validate_on_submit():
            movie_title = request.form["title"]
            response = requests.get(TMDB_SEARCH_URL, params={"api_key": TMDB_API, "query": movie_title}).json()
            movie_list = [movie for movie in response["results"]]
            return render_template("select.html", movies=movie_list)
        return render_template("add.html", form=form)


    @app.route("/find")
    def find_movie():
        movie_api_id = request.args.get("id")
        if movie_api_id:
            movie_api_url = f"{MOVIE_INFO_URL}/{movie_api_id}"
            response = requests.get(movie_api_url, params={"api_key": TMDB_API, "language": "en-US"}).json()
            new_movie = Movie(
                title=response["title"],
                year=response["release_date"].split("-")[0],
                description=response["overview"],
                img_url=f"https://image.tmdb.org/t/p/w500/{response['poster_path']}"
            )
            db.session.add(new_movie)
            db.session.commit()
            movie = Movie.query.filter_by(title=response["title"]).first()
            return redirect(url_for("rate_movie", id=movie.id))


    if __name__ == '__main__':
        app.run(debug=True)
