"""Models used for the SQLAlchemy database."""
from datetime import datetime

from moontracker.extensions import db


class Alert(db.Model):
    """Object to add to database."""

    __table_args__ = {'extend_existing': True}
    __tablename__ = 'alerts'
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(80), nullable=False)
    price = db.Column(db.Float, nullable=False)
    above = db.Column(db.Integer, nullable=False)
    phone_number = db.Column(db.String(80), nullable=False)


class User(db.Model):
    """Object for user database entries."""

    __table_args__ = {'extend_existing': True}
    __tablename__ = 'users'
    id = db.Column('user_id', db.Integer, primary_key=True)
    username = db.Column('username', db.String(80), unique=True, index=True,
                         nullable=False)
    pw_hash = db.Column('pw_hash', db.String(80), nullable=False)
    phone_number = db.Column('phone_number', db.String(80), nullable=False)
    registered_on = db.Column('registered_on', db.DateTime, nullable=False)

    def __init__(self, username, pw_hash, phone_number):
        """Initialize User object.

        Args:
            username: The username string.
            pw_hash: Password hash value.
            phone_number: User's phone number.
        """
        self.username = username
        self.pw_hash = pw_hash
        self.phone_number = phone_number
        self.registered_on = datetime.utcnow()

    def is_authenticated(self):
        """Authenticate user."""
        return True

    def is_active(self):
        """Check if user is active."""
        return True

    def is_anonymous(self):
        """Check if user is anonymous."""
        return False

    def get_id(self):
        """Get user Id."""
        return str(self.id)
