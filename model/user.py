class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    name = db.Column(db.String(150), nullable=False)
    google_id = db.Column(db.String(255), unique=True)
    leetcode_username = db.Column(db.String(150), nullable=True)
    display_submissions = db.Column(db.Boolean, default=True)