#import libraries
from flask import (Flask, render_template, abort, jsonify, 
                    request, redirect, url_for)
from model import db, save_db

#global flask object-app
app = Flask(__name__)

#view function for welcome page
@app.route("/welcome")
def date():
    return render_template(
        "welcome.html",
        cards=db
    )

#view function for card view
#accept index of card from url and render the particular card page
@app.route("/card/<int:index>")
def card_view(index):
    try:
        card = db[index]
        return render_template(
        "card.html",
        card=card,
        index=index,
        max_index=len(db)-1
    )
    except IndexError:
        abort(404)

@app.route('/api/card/<int:index>')
def api_card_details(index):
    try:
        return db[index]
    except IndexError:
        abort(404)

@app.route('/api/card/')
def api_card_list():
    return jsonify(db)

#view function to add new cards
@app.route('/add_card', methods=["GET", "POST"])
def add_card():
    if request.method == "POST":
        new_card = {"agent": request.form['agent'],
        "type": request.form['type']}
        db.append(new_card)
        save_db()
        return redirect(url_for('card_view', index=len(db)-1))

    else:
        return render_template("add_card.html")

#view function to remove existing cards
@app.route('/remove_card/<int:index>', methods=["GET", "POST"])
def remove_card(index):
    try:
        if request.method == "POST":
            del db[index]
            save_db()
            return redirect(url_for('date'))
        else:
            return render_template('remove_card.html', card=db[index])
    except IndexError:
        abort(404)