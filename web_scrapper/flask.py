from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import uuid

app = Flask(__name__)
# Update this URI to your actual PostgreSQL credentials
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://username:password@hostname:port/database_name'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    ssh_identifier = db.Column(db.String(36), unique=True, nullable=False)

@app.before_first_request
def create_tables():
    db.create_all()

@app.route('/register', methods=['POST'])
def register():
    username = request.json['username']
    if User.query.filter_by(username=username).first():
        return jsonify({'message': 'Username already exists'}), 400
    
    ssh_identifier = str(uuid.uuid4())
    new_user = User(username=username, ssh_identifier=ssh_identifier)
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({'username': username, 'ssh_identifier': ssh_identifier}), 201

@app.route('/login', methods=['POST'])
def login():
    username = request.json['username']
    user = User.query.filter_by(username=username).first()
    if user:
        return jsonify({'message': 'Login successful', 'ssh_identifier': user.ssh_identifier}), 200
    else:
        return jsonify({'message': 'User not found'}), 404

if __name__ == '__main__':
    app.run(debug=True)
