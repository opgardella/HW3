# Olivia Gardella
# SI364 - Midterm
# API link: https://newsapi.org/docs/
# https://newsapi.org/docs/endpoints/top-headlines

###############################
####### SETUP (OVERALL) #######
###############################

# Import statements
import os
from flask import Flask, render_template, session, redirect, url_for, flash, request
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, ValidationError # Note that you may need to import more here! Check out examples that do what you want to figure out what.
from wtforms.validators import Required, Length # Here, too
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager, Shell
import os
import requests
import json

## App setup code
basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
app.debug = True

## All app.config values
# code from hw3 used for setup
app.config['SECRET_KEY'] = 'this is a hard to guess string from si364'
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://postgres:si364@localhost/gardellaMidterm"
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

## Statements for db setup (and manager setup if using Manager)
db = SQLAlchemy(app)
manager = Manager(app)

## API key
API_KEY = '93576556daae407cb66107833a825ec3'


######################################
######## HELPER FXNS (If any) ########
######################################




##################
##### MODELS #####
##################

class Name(db.Model):
    __tablename__ = "names"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    sources = db.relationship('Sources',backref='Name')

    def __repr__(self):
        return "{} (ID: {})".format(self.name, self.id)


class News(db.Model):
    __tablename__ = "news"
    id = db.Column(db.Integer, primary_key=True)
    article = db.Column(db.String(300))

    def __repr__(self):
        return "{} (ID: {})".format(self.article, self.id)


class Sources(db.Model):
    __tablename__ = "sources"
    id = db.Column(db.Integer, primary_key=True)
    source = db.Column(db.String(50))
    name_id = db.Column(db.Integer,db.ForeignKey("names.id"))

    def __repr__(self):
        return "{} (ID: {})".format(self.source, self.id)




###################
###### FORMS ######
###################

class NameForm(FlaskForm):
    name = StringField("Please enter your name.",validators=[Required()])
    submit = SubmitField()

class NewsForm(FlaskForm):
    keyword = StringField('Enter a keyword:', validators=[Required(), Length(1,100)])
    submit = SubmitField()

class SourcesForm(FlaskForm):
    name = StringField("Enter your name:", validators=[Required()])
    source = StringField("Enter one source where you get news:", validators=[Required()])
    submit = SubmitField()

    #custom validator
    def validate_source(self,field):
        source = field.data
        special_chrs = ['@', '!', '#']
        for c in special_chrs:
            if c in source:
                raise ValidationError("Source should not contain the characters '@', '!', or '#'!")




#######################
###### VIEW FXNS ######
#######################

@app.route('/', methods=['GET', 'POST'])
def home():
    form = NameForm() # User should be able to enter name after name and each one will be saved, even if it's a duplicate! Sends data with GET
    if form.validate_on_submit():
        name = form.name.data
        newname = Name(name=name)
        db.session.add(newname)
        db.session.commit()
        return redirect(url_for('all_names'))
    return render_template('base.html',form=form)


@app.route('/names')
def all_names():
    names = Name.query.all()
    return render_template('name_example.html',names=names)


@app.route('/news', methods=['GET', 'POST'])
def news():
    form = NewsForm()
    num_news = len(News.query.all())

    if form.validate_on_submit():
        keyword = form.keyword.data #what they typed in

        params = {}
        params['apiKey'] = API_KEY
        params['q'] = keyword
        baseurl = 'https://newsapi.org/v2/top-headlines?'
        response = requests.get(baseurl, params = params)
        response_dict = json.loads(response.text)
        if len(response_dict['articles']) > 0:
            title = response_dict['articles'][0]['title']

            key_word = News(article=title)

            db.session.add(key_word)
            db.session.commit()
            return redirect(url_for('news_results'))
        else:
            flash('There are no recent headlines pertaining to this keyword, try a different keyword!')
            return redirect(url_for('news'))
    return render_template('news.html', form=form, num_news=num_news)


@app.route('/news_results')
def news_results():
    news = News.query.all()
    return render_template('news_results.html', news=news)


@app.route('/sources', methods=['GET', 'POST'])
def sources():
    form = SourcesForm()
    if form.validate_on_submit():
        name = form.name.data
        source = form.source.data

        #see if there is already someone with that name
        #if there is, save it in variable: name
        #if not, create it and add to database
        name_in_db = Name.query.filter_by(name=name).first()
        if not name_in_db:
            name_in_db = Name(name=name)
            db.session.add(name_in_db)
            db.session.commit()

        #if that source already exists with this name id
        #flash message that it already exists
        #and refresh page
        source_in_db = Sources.query.filter_by(source=source, name_id=name_in_db.id).first()
        if source_in_db:
            flash('This source already exists for this name!')
            return redirect(url_for('sources'))
        source = Sources(name_id=name_in_db.id, source=source)
        db.session.add(source)
        db.session.commit()
        flash('Source successfully saved!')
        return(redirect(url_for('sources')))

    sources = Sources.query.all()
    all_sources = []
    for s in sources:
        name = Name.query.filter_by(id=s.name_id).first()
        all_sources.append((s,name))
    print(all_sources)

    return render_template('sources.html',form=form, all_sources=all_sources)


# 404 Error handler
# got code from hw3 (didn't directly copy, just similar)
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404error.html'), 404




## Code to run the application
if __name__ == '__main__':
    db.create_all()
    manager.run()
    app.run(use_reloader=True,debug=True)
