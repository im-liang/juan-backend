import os
import uuid

from flask import Flask, request, jsonify
from google.oauth2 import id_token
from google.auth.transport import requests
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity, create_access_token
import asyncio
import aiohttp

from db.db import get_all_users, insert_user, get_user_by_email
from helper.leetcode import fetch_submissions_for_users

app = Flask(__name__)

# jwt setup
app.config["JWT_SECRET_KEY"] = os.environ['JWT_SECRET_KEY']
jwt = JWTManager(app)

@app.route("/api/submissions", methods=["GET"])
@jwt_required()
def get_submissions():
    # Assuming get_all_users() retrieves the list of users
    userList = get_all_users()

    # Check if the user list is empty
    if not userList:
        return jsonify({"message": "No users found"}), 404
    
    # Call the helper function to fetch submissions concurrently with rate-limiting handling
    try:
        submissions = asyncio.run(fetch_submissions_for_users(userList))
        # If no submissions found, return a message
        if not submissions:
            return jsonify({"message": "No submissions found for users."}), 404
        
        # Return the distinct submissions data as JSON response
        return jsonify(submissions)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/user", methods=["PATCH"])
@jwt_required()
def add_submission():
    current_user = get_jwt_identity()
    data = request.json
    insert_user(data)
    return jsonify({"message": "Submission added successfully"}), 201

@app.route('/api/auth/google/callback', methods=['POST'])
def google_auth_callback():
    token = request.json.get('token')
    try:
        # Verify the Google ID token
        GOOGLE_CLIENT_ID = os.environ['GOOGLE_CLIENT_ID']
        idinfo = id_token.verify_oauth2_token(token, requests.Request(), GOOGLE_CLIENT_ID)
        email = idinfo.get('email')
        name = idinfo.get('name')

        # Check if the user exists in Cosmos DB
        users = get_user_by_email(email)
        print(users)
        if not users:
            # Create a new user if not exists
            user = {
                "id": str(uuid.uuid4()),
                "email": email,
                "name": name,
                "leetcode_username": None,
                "share_submissions": False,
            }
            insert_user(user)
        else:
            user = users[0]

        # Create a JWT token
        access_token = create_access_token(identity=user["email"])
        return jsonify(access_token=access_token), 200
    except ValueError:
        return jsonify({"error": "Invalid token"}), 400

if __name__ == "__main__":
    app.run(debug=True)
