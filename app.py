#import libraries
from wsgiref.validate import validator
from flask import (Flask, render_template, abort, jsonify, 
                    request, redirect, send_from_directory, url_for, flash)
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, Column, Integer, String, ForeignKey, insert, create_engine
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed
from wtforms import StringField, TextAreaField, SubmitField, SelectField, FileField
from wtforms.validators import InputRequired, DataRequired
from werkzeug.utils import secure_filename
#from model import db, save_db
import pdb
import os
import datetime
from secrets import token_hex

#global flask object->app
app = Flask(__name__)

#get the absolute path for this file
basedir = os.path.abspath(os.path.dirname(__file__))

#configurations for SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///getting_started.db'             #used for connecting to database
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False                               #do not track modifications
app.config['SECRET_KEY'] = 'secretkey' 
app.config['ALLOWED_IMAGE_EXTENSIONS'] = ["jpeg", "png", "jpg"]
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 
app.config['IMAGE_UPLOADS'] = os.path.join(basedir, "uploads")                      

#object of SQLAlchemy class 
sqla = SQLAlchemy(app)

class FlashCards(sqla.Model):
    #class representing the database table FlashCards. Inherits from Model class.
    __tablename__ = 'agent_list'
    _id = sqla.Column("id", sqla.Integer, primary_key=True)
    agent_name = sqla.Column(sqla.String(50), unique=True)
    agent_type = sqla.Column(sqla.String(50))
    agent_image = sqla.Column(sqla.String(100))

    def __init__(self, agent_name, agent_type, filename=""):
        self.agent_name = agent_name
        self.agent_type = agent_type
        self.agent_image = filename
        
class AgentCategory(sqla.Model):
    #class representing the database table for agent types
    __tablename__ = 'agent_category'
    _id = sqla.Column("id", sqla.Integer, primary_key=True)
    category = sqla.Column(sqla.String(50))

    def __init__(self, category):
        self.category = category

class AddCardForm(FlaskForm):
    #class representing add card form
    name = StringField("Name",  validators=[InputRequired("Input is Required!"), DataRequired("Data is Required!")])
    type = SelectField("Type", coerce=int)
    image = FileField("Image", validators=[FileAllowed(app.config['ALLOWED_IMAGE_EXTENSIONS'], "Images Only!")])
    submit = SubmitField("Create")

class EditCardForm(AddCardForm):
    submit = SubmitField("Update")

class AddAgentCategoryForm(FlaskForm):
    #class representing add agent category form
    category = StringField("Category", validators=[InputRequired("Input is Required!"), DataRequired("Data is Required!")])
    submit = SubmitField("Add")

@app.route("/uploads/<filename>")
def uploads(filename):
    return send_from_directory(app.config['IMAGE_UPLOADS'], filename)

#view function for welcome page
@app.route("/welcome")
def welcome():
    """query all records from database and pass the object to welcome template"""
    flashCards = FlashCards.query.all()
    return render_template(
        "welcome.html",
 #       cards=db
        cards = flashCards
    )

#view function for card view
#accept index of card from url and render the particular card page
@app.route("/card/<int:index>")
def card_view(index):
    try:
#        card = db[index]
        max_id = sqla.session.query(func.max(FlashCards._id)).scalar()
        min_id = sqla.session.query(func.min(FlashCards._id)).scalar()
        next_index = index + 1

        """check if the index passed is valid"""
        if index > 0 and index <= max_id:
            """get the record for the current index from database"""
            card = FlashCards.query.filter_by(_id=index).first()
            type = AgentCategory.query.filter_by(_id=card.agent_type).first()
            """compute the index/id for next available record in database"""
            while next_index <= max_id and FlashCards.query.filter_by(_id=next_index).first() is None:
                next_index += 1
            return render_template(
            "card.html",
            card=card,
            next_index=next_index,
            curr_index=index,
            max_index=max_id,
            min_index=min_id,
            type=type
        )
        else:
            raise IndexError
    except IndexError:
        abort(404)

#view function to add new cards
@app.route('/add_card', methods=["GET", "POST"])
def add_card():
    """object of AddCardForm class"""
    form = AddCardForm()
    """fetch all the available categories as tuple from database and assign as choices"""
    c = [(item._id, item.category) for item in (AgentCategory.query.all())]
    form.type.choices = c

    """check if the request is POST and all fields have valid input"""
    if form.validate_on_submit():
        filename = ''
        if form.image.data.filename:
            filename = generateUniqueName(form.image.data.filename)
            """check if filename is secure"""
            filename = secure_filename(filename)
            """save the image in uploads folder"""
            form.image.data.save(os.path.join(app.config['IMAGE_UPLOADS'], filename))
#        new_card = {"agent": request.form['agent'],
#
#         "type": request.form['type']}
#        db.append(new_card)
#        save_db()
        """getting the form data and commiting to database"""
#        name = request.form['agent']
#        type = request.form['type']
        """accessing the form data using Flask-wtf"""
        name = form.name.data
        type = form.type.data
        fc = FlashCards(name, type, filename)
        sqla.session.add(fc)
        sqla.session.commit()
        
        """get the id of this record"""
        id = fc._id
        """add a success flash message"""
        flash("Card {} has been created successfully.".format(fc.agent_name), "success")
#        return redirect(url_for('card_view', index=len(db)-1))
        return redirect(url_for('card_view', index=id))
    
    if form.errors:
        flash("{}".format(form.errors), 'danger')
    return render_template("add_card.html", form=form)

#view function to remove existing cards
@app.route('/remove_card/<int:index>', methods=["GET", "POST"])
def remove_card(index):
    try:
        fc = FlashCards.query.filter_by(_id=index).first()
        if request.method == "POST":
#            del db[index]
#            save_db()
            FlashCards.query.filter_by(_id=index).delete()
            sqla.session.commit()
            flash("Card {} has been removed successfully.".format(fc.agent_name), "success")
            return redirect(url_for('welcome'))
        else:
            return render_template('remove_card.html', 
            card=fc,
            type = AgentCategory.query.filter_by(_id=fc.agent_type).first()
            )
    except IndexError:
        abort(404)

#view function for updating card
@app.route('/edit_card/<int:index>', methods=["GET", "POST"])
def edit_card(index):
    form = EditCardForm()
    c = [(item._id, item.category) for item in (AgentCategory.query.all())]
    form.type.choices = c
    card = FlashCards.query.get_or_404(index)
    if form.validate_on_submit():
        card.agent_name = form.name.data
        card.agent_type = form.type.data
        sqla.session.commit()
        flash("Card {} updated!".format(card.agent_name))
        return redirect(url_for('welcome'))
    
    form.name.data = card.agent_name
    if form.errors:
        flash("{}".format(form.errors), 'danger')
    return render_template('edit_card.html', card=card, form=form)

#view function to add agent category
@app.route('/add_category', methods=["GET", "POST"])
def add_category():
    form = AddAgentCategoryForm()
    if request.method == "POST":
        category = form.category.data
        c = AgentCategory(category)
        sqla.session.add(c)
        sqla.session.commit()
        flash("Category {} has been added successfully".format(c.category), "success")
        return redirect(url_for('welcome'))
    else:
        return render_template('add_category.html',form=form)
        
@app.route('/categories')
def category_view():
    categories = AgentCategory.query.all()
    return render_template('category.html', categories=categories)

#generate a unique filename for image
def generateUniqueName(name):
    format = '%Y%m%dT%H%M%S'
    now = datetime.datetime.utcnow().strftime(format)
    random_string = token_hex(2)
    return(random_string + "_" + now + "_" + name)

if __name__ == '__main__':
    sqla.create_all()               #create the database
    app.run(debug=True)