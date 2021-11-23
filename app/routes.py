from app import app
from app.models import *
from flask import jsonify, request, render_template
from datetime import datetime
from Etsy import Etsy
import sqlalchemy
import smtplib, ssl, os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


# ---------------------------------- FUNCTIONS ---------------------------------- #

# add the specified transaction to the db, with associated Buyer and Poster
def add_transaction_and_others(etsy_transaction, E=Etsy()):
    # Get buyer_user_id and check if buyer exists in db
    buyer_user_id = etsy_transaction['buyer_user_id']
    b = Buyer.query.filter_by(id=buyer_user_id).first()
    # If not, add the buyer to the db
    if b is None:
        etsy_receipt = E.get_receipt(etsy_transaction['receipt_id'])
        b = Buyer(
            id=buyer_user_id,
            etsy_email=etsy_receipt['buyer_email']
        )

        db.session.add(b)
    
    # Create the Transaction
    t = Transaction(
        id = etsy_transaction['transaction_id'],
        timestamp = datetime.fromtimestamp(etsy_transaction['creation_tsz']),
        sku = etsy_transaction['product_data']['sku'],
        receipt_id = etsy_transaction['receipt_id'],
        quantity = etsy_transaction['quantity'],
        shipped = etsy_transaction['shipped_tsz'] is not None,
        buyer_id=b.id
    )

    # Create each Poster required for the Transaction
    for i in range(t.quantity):
        p = Poster(
            sent=etsy_transaction['shipped_tsz'] is not None,
            transaction_id=t.id
        )
        db.session.add(p)
        t.posters.append(p)

    db.session.add(t)
    db.session.commit()
    
    return t

def sendemail(receiver_email, subject, text):
    sender_email = os.environ['EMAIL_ADDRESS']
    password = os.environ['EMAIL_PASSWORD']

    # Try to log in to server and send email
    try:
        server = smtplib.SMTP("smtp.gmail.com",587)
        server.starttls(context=ssl.create_default_context()) # Secure the connection
        server.login(sender_email, password)

        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = sender_email
        message["To"] = receiver_email

        message.attach(MIMEText(text, "plain"))

        server.sendmail(sender_email, receiver_email, message.as_string())
    except Exception as e:
        # Print any error messages to stdout
        print(e)
    finally:
        server.quit()

def get_poster_size(transaction_id):
    t = Transaction.query.filter_by(id=transaction_id).first()
    return t.poster_scale


# ---------------------------------- FORMS ---------------------------------- #

@app.route('/form/<poster_id>', methods=['GET', 'POST'])
def starmap_form(poster_id):
    p = Poster.query.filter_by(id=poster_id).first()
    if request.method == 'GET':
        t = Transaction.query.filter_by(id=p.transaction_id).first()

        if t.is_digital:
            if not p.sent:
                return render_template('digital_starmap_form.html', response=Response(), poster_id=poster_id)
            else:
                return render_template('disabled_digital_starmap_form.html', response=p.response, poster_id=poster_id)
        else:
            if not p.sent:
                return render_template('physical_starmap_form.html', response=Response(), poster_id=poster_id)
            else:
                return render_template('disabled_physical_starmap_form.html', response=p.response, poster_id=poster_id)

        # TODO add sorry no edits page for sent posters
        
    elif request.method == 'POST':
        button_value = request.form.get('button')
        if button_value == 'save':
            response_datetime = str(request.form.get('map_date')) + ' ' + str(request.form.get('map_time'))
            r = Response(
                timestamp = datetime.now(),
                # All Responses
                map_datetime = datetime.strptime(response_datetime, "%Y-%m-%d %H:%M"),
                map_written_datetime = request.form.get('map_written_datetime'),
                message = request.form.get('message'),
                map_written_address = request.form.get('map_written_location'),
                size = request.form.get('image_scale') or get_poster_size(p.transaction_id),
                latitude = request.form.get('lat'),
                longitude = request.form.get('long'),
                # Starmap Only
                colour = request.form.get('colour_scheme'),
                font = request.form.get('font'),
                # Watercolour Only
                show_conlines = request.form.get('show_conlines'),
                map_background = request.form.get('map_background'),
                # Relationships
                poster_id = poster_id
                )

            # Add Response to Poster and commit to db
            p.response = r
            p.responded = True
            db.session.add(p)
            db.session.add(r)
            db.session.commit()
            return render_template('disabled_digital_starmap_form.html', response=r, poster_id=poster_id)
            # TODO email copy of form to user


# ---------------------------------- BUYER ---------------------------------- #

@app.route('/buyer', methods=['GET'])
def all_buyers():
    # Return all Buyers as dicts
    if request.method == 'GET':
        bs = Buyer.query.all()
        return jsonify([b.dict for b in bs]), 200

@app.route('/buyer/<buyer_id>', methods=['GET'])
def get_buyer(buyer_id):
    # Return specified Buyer as dict
    if request.method == 'GET':
        b = Buyer.query.filter_by(id=buyer_id).first()
        return jsonify(b.dict), 200

# ---------------------------------- TRANSACTION ---------------------------------- #

@app.route('/transaction', methods=['GET', 'PUT'])
def all_transactions():
    # Return all transactions as dicts
    if request.method == 'GET':
        ts = Transaction.query.all()
        return jsonify([t.dict for t in ts]), 200

    # Get all open transactions from Etsy and put them in database
    elif request.method == 'PUT':
        added = [] # store added transactions for returning
        E = Etsy()
        etsy_open_transactions = E.get_open_transactions()
        # Add all open transactions, if they don't already exst in db
        for etsy_transaction in etsy_open_transactions.values():
            query = Transaction.query.filter_by(id=etsy_transaction['transaction_id']).first()
            if query is None:
                t = add_transaction_and_others(etsy_transaction, E=E)
                added.append(t)
        # Return ids of added Transactions
        return jsonify([t.id for t in added]), 200

@app.route('/transaction/open', methods=['GET'])
def all_open_transactions():
    # Return all transactions as dicts
    if request.method == 'GET':
        ts = Transaction.query.filter_by(shipped=False).all()
        return jsonify([t.dict for t in ts]), 200

@app.route('/transaction/<transaction_id>', methods=['GET', 'PUT', 'DELETE'])
def transaction(transaction_id):
    # Return specified Transaction as dict
    if request.method == 'GET':
        t = Transaction.query.filter_by(id=transaction_id).first()
        return jsonify(t.dict), 200

    # Put the specified transaction
    elif request.method == 'PUT':
        E = Etsy()
        etsy_transaction = E.get_transaction(transaction_id)
        t = add_transaction_and_others(etsy_transaction, E=E)
        return jsonify(t.dict), 200
    
    # Delete the specified Transaction and associated Posters/Responses
    elif request.method == 'DELETE':
        # Get the Transaction, its Posters/Responses
        t = Transaction.query.filter_by(id=transaction_id).first()
        ps = t.posters
        rs = [p.response for p in ps]

        # Delete Transaction and all found Posters/Responses 
        db.session.delete(t)
        for p in ps:
            db.session.delete(p)
        for r in rs:
            # Responses not guaranteed to exist so check first
            if r is not None:
                db.session.delete(r)

        db.session.commit()
        return {'success' : 'Transaction and orphaned dependents deleted'}, 200

@app.route('/transaction/<transaction_id>/mark_shipped', methods=['PATCH'])
def mark_transaction_shipped(transaction_id):
    # Return specified Transaction as dict
    if request.method == 'PATCH':
        t = Transaction.query.filter_by(id=transaction_id).first()
        t.shipped = True
        db.session.commit()
        return {'success' : 'Transaction and child Posters marked shipped and sent'}, 200


# ---------------------------------- POSTER ---------------------------------- #

@app.route('/poster', methods=['GET'])
def all_posters():
    # Return all Posters as dicts
    if request.method == 'GET':
        ps = Poster.query.all()
        return jsonify([p.dict for p in ps]), 200

@app.route('/poster/<poster_id>', methods=['GET'])
def poster(poster_id):
    # Return specified Poster as dict
    if request.method == 'GET':
        p = Poster.query.filter_by(id=poster_id).first()
        return jsonify(p.dict), 200

@app.route('/poster/<poster_id>/response', methods=['GET', 'POST', 'PATCH'])
def poster_response(poster_id):
    p = Poster.query.filter_by(id=poster_id).first()

    # Return Response for specified Poster as dict
    if request.method == 'GET':
        if p.response is None:
            return {'success' : 'Request succeeded but Poster Response is None.'}, 200
        else:
            return jsonify(p.response.dict), 200
    
    if request.method == 'POST':
        # Add a Response to the specified Poster and commit to db
        # First check if Poster already has Response
        if p.response is None:
            # Create the Response from the request json
            response_data = request.get_json()
            r = Response(
                timestamp = datetime.now(),
                map_datetime = datetime.fromtimestamp(response_data['map_datetime']),
                map_written_datetime = response_data['map_written_datetime'],
                message = response_data['message'],
                map_written_address = response_data['map_written_address'],
                size = response_data['size'],
                latitude = response_data['latitude'],
                longitude = response_data['longitude'],
                colour = response_data['colour'],
                font = response_data['font'],
                show_conlines = response_data.get('show_conlines'),
                map_background = response_data.get('map_background'),
            )
            # Add Response to Poster and commit to db
            p.response = r
            p.responded = True
            db.session.add(p)
            db.session.add(r)
            db.session.commit()
            return jsonify(r.dict), 200
        else:
            # if Poster has response, tell user to PATCH instead
            return {'error': 'Response exists, please use PATCH instead.'}, 409
    
    if request.method == 'PATCH':
        # PATCH the Response for the specified Poster
        # Get the id of the response from the Poster
        response_id = p.response.id

        changes = request.get_json()

        if changes.get('map_datetime'):
            changes['map_datetime'] = datetime.fromtimestamp(changes['map_datetime'])

        # Use request json to update multiple columns simultaneously for one Response
        try:
            Response.query.filter_by(id=response_id).update(request.get_json())
        except sqlalchemy.exc.InvalidRequestError:
            return {'error' : 'Column does not exist'}, 406

        db.session.commit()

        # Get revised Response so it can be returned
        r = Response.query.filter_by(id=response_id).first()
    
        if r is None:
            return {'error' : 'Response not found'}, 404

        return jsonify(r.dict), 200

@app.route('/poster/<poster_id>/mark_approved', methods=['PATCH'])
def poster_approved(poster_id):
    # Mark specified Poster as approved
    if request.method == 'PATCH':
        t = Poster.query.filter_by(id=poster_id).first()
        t.approved = True
        db.session.commit()
        return {'success' : 'Poster marked approved'}, 200

@app.route('/poster/<poster_id>/mark_sent', methods=['PATCH'])
def poster_sent(poster_id):
    # Mark specified Poster as approved
    if request.method == 'PATCH':
        p = Poster.query.filter_by(id=poster_id).first()
        t = Transaction.query.filter_by(id=p.transaction_id).first()
        p.sent = True

        message = ''

        if t.is_digital:
            posters_sent = [p.sent for p in t.posters]
            if all(posters_sent):
                t.shipped = True
                e = Etsy()
                e.mark_complete(t.receipt_id)
                message = ' and order is complete'

        db.session.commit()
        return {'success' : 'Poster marked sent' + message}, 200

@app.route('/poster/<poster_id>/request_edit', methods=['PATCH'])
def poster_request_edit(poster_id):
    # Return Response for specified Poster as dict
    if request.method == 'PATCH':
        p = Poster.query.filter_by(id=poster_id).first()
        text = request.json['text']
        email = os.environ['EMAIL_ADDRESS']

        message = f"""\
            Hello Me, 

            poster_id = {poster_id}
            edit_requested:
            
            {text}

            Now go do.
            """

        sendemail(email, 'Edit Request Received', message)
        
        p.edit_requested = True
        db.session.commit()

        return {'success' : 'Edit request received'}, 200


# ---------------------------------- RESPONSE ---------------------------------- #

@app.route('/response', methods=['GET'])
def all_responses():
    # Return all Responses as dicts
    if request.method == 'GET':
        rs = Response.query.all()
        return jsonify([r.dict for r in rs]), 200

@app.route('/response/<response_id>', methods=['GET'])
def response(response_id):
    # Return specified Response as dict
    if request.method == 'GET':
        r = Response.query.filter_by(id=response_id).first()
        return jsonify(r.dict), 200
