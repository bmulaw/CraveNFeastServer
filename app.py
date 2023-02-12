from flask import Flask, jsonify, request, make_response, Blueprint
import firebase_admin
import requests
from firebase_admin import credentials, initialize_app, firestore
import os
from dotenv import load_dotenv
import requests
import json
from flask_cors import CORS

load_dotenv()

# Database
cred = credentials.Certificate("key.json")
default_app = firebase_admin.initialize_app(cred)

db = firestore.client()
# user_Ref = db.collection('Account')

#Flask/CORS
app = Flask(__name__)

app.config['CORS_HEADERS'] = 'Content-Type'
CORS(app)

# API
Edmam_ID = os.environ.get("Edmam_ID")
Edmam_Key = os.environ.get("Edmam_Key")

# ROUTES

# Create Account


@app.route('/register', methods=["POST"])
def create_account():
    request_body = request.get_data()
    request_body = json.loads(request_body)
    data = {
        "username": request_body["user"],
        "password": request_body["pwd"]
    }
    print(data)
    #TODO:Make sure username is unique
    db.collection('Account').document(data['username']).set(data)

    return make_response(jsonify({
        'message': 'Account was created'
    }), 201)

# Delete Account


@app.route('/account/<account_id>', methods=["DELETE"])
def delete_account(account_id):
    try:
        db.collection('Account').document(account_id).delete()
        response_body = {
            'message': f'Account {account_id} was deleted.'}
        return make_response(jsonify(response_body), 200)
    except Exception as e:
        return f"An Error Occured: {e}"


# Update account to change name or email
@app.route('/account/<account_id>', methods=["PUT"])
def update_account(account_id):
    try:
        db.collection('Account').document(account_id).update(request.json)
        return jsonify({'message': f'Account {account_id} was updated.'}), 200
    except Exception as e:
        return f"An Error Occurred: {e}"

#Create Favorites
@app.route('/account/<account_id>/favorite', methods=["POST"])
def add_favorites(account_id):
    try:
        request_body = request.get_data()
        request_body = json.loads(request_body)
        all_favorites = db.collection('Account').document(account_id).collection('Favorites').stream()
        favorites={}
        for doc in all_favorites:
            favorites[doc.id]= doc.to_dict()
        if request_body["recipe"] in favorites.values():
            for id in favorites.keys():
                if request_body["recipe"] == favorites[id]:
                    db.collection('Account').document(account_id).collection('Favorites').document(id).delete()
        else:
            db.collection('Account').document(account_id).collection('Favorites').add(request_body['recipe'])
        return jsonify({'message': f'Favorite was added to account {account_id}.'}), 200
    except Exception as e:
        return f"An Error Occurred: {e}"

# Read one username
@app.route('/auth', methods=["GET"])
def read_account():
    # request_body = json.loads(request_body)
    # docs = db.collection('Account').document(user_name).stream()
    # return (jsonify(docs), 200)
    user=request.args.get("user")
    password=request.args.get("pwd")
    
    try:
        doc = db.collection("Account").document(user).get().to_dict()
        if password == doc["password"]:
            response_body = {'message': f'User #{user} has signed in.'}
            return make_response(jsonify(response_body), 200)
        else:
            response_body = {'message': f'Password is incorrect.'}
            return make_response(jsonify(response_body), 400)
    except:
        response_body = {'message': f'User does not exist.'}
        return make_response(jsonify(response_body), 400)


# Read ALL Favorites
@app.route('/account/<account_id>/favorites', methods=["GET"])
def read_all_favorites(account_id):
    docs = db.collection('Account').document(
        account_id).collection('Favorites').stream()
    doc_list = []
    for doc in docs:
        doc_list.append(doc.to_dict())
    return (jsonify(doc_list), 200)

# Delete One Favorite
@app.route('/account/<account_id>/favorites/<favorites_id>', methods=["DELETE"])
def delete_one_favorite(account_id, favorites_id):
    try:
        # favorites_num = request.args.get('favorites_id')
        db.collection('Account').document(account_id).collection(
            'Favorites').document(favorites_id).delete()
    # db.collection(‘Accounts’).document(account_id).collection(‘Favorites’).document(favorites_id)
        # db.collection('Favorites').document(favorites_id).delete()
        response_body = {
            'message': f'Favorites #{favorites_id} was deleted.'}
        return make_response(jsonify(response_body
                                     ), 200)
    except Exception as e:
        return f"An Error Occured: {e}"


# Get specific Recipe

@app.route('/api/recipes/v2', methods=["GET"])
def get_recipes():
    q_query = request.args.get("q")
    options = {
        'app_id': Edmam_ID,
        'app_key': Edmam_Key,
        'q': q_query,
        'type': 'public'

    }
    url = 'https://api.edamam.com/api/recipes/v2'
    if not q_query:
        return {"message": "must provide q parameters"}
    r = requests.get(url, params=options)
    response=r.json()
    size = len(response['hits'])
    data_list= []
    for i in range(size):
        the_response = response["hits"][i]["recipe"]
        data ={
            "image":the_response['image'],
            "url": the_response['url'],
            'label': the_response['label'],
            'cuisineType': the_response['cuisineType'],
            'ingredientLines': the_response['ingredientLines']
        }
        data_list.append(data)
    return make_response(jsonify(data_list))


if __name__ == '__main__':
    app.run(debug=True)
