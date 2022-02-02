#import libraries
from enum import unique
from flask import (Flask, render_template, abort, jsonify, 
                    request, redirect, url_for)
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from model import db, save_db
from datetime import datetime

#global flask object->app
app = Flask(__name__)

#configurations for SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///getting_started.db'             #used for connecting to database
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False                               #do not track modifications

#object of SQLAlchemy class 
sqla = SQLAlchemy(app)

class FlashCards(sqla.Model):
    #class representing the database table FlashCards. Inherits from Model class.
    _id = sqla.Column("id", sqla.Integer, primary_key=True)
    agent_name = sqla.Column(sqla.String(50), unique=True)
    agent_type = sqla.Column(sqla.String(50))

    def __init__(self, agent_name, agent_type):
        self.agent_name = agent_name
        self.agent_type = agent_type
        
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
            """compute the index/id for next available record in database"""
            while next_index <= max_id and FlashCards.query.filter_by(_id=next_index).first() is None:
                next_index += 1
            return render_template(
            "card.html",
            card=card,
            next_index=next_index,
            curr_index=index,
            max_index=max_id,
            min_index=min_id
        )
        else:
            raise IndexError
    except IndexError:
        abort(404)

#view function to add new cards
@app.route('/add_card', methods=["GET", "POST"])
def add_card():
    if request.method == "POST":
#        new_card = {"agent": request.form['agent'],
#        "type": request.form['type']}
#        db.append(new_card)
#        save_db()
        """getting the form data and commiting to database"""
        name = request.form['agent']
        type = request.form['type']
        fc = FlashCards(name, type)
        sqla.session.add(fc)
        sqla.session.commit()
        
        """get the id of this record"""
        id = fc._id
#        return redirect(url_for('card_view', index=len(db)-1))
        return redirect(url_for('card_view', index=id))

    else:
        return render_template("add_card.html")

#view function to remove existing cards
@app.route('/remove_card/<int:index>', methods=["GET", "POST"])
def remove_card(index):
    try:
        if request.method == "POST":
#            del db[index]
#            save_db()
            FlashCards.query.filter_by(_id=index).delete()
            sqla.session.commit()
            return redirect(url_for('welcome'))
        else:
            return render_template('remove_card.html', card=FlashCards.query.filter_by(_id=index).first())
    except IndexError:
        abort(404)

if __name__ == '__main__':
    sqla.create_all()               #create the database
    app.run(debug=True)