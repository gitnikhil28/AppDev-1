from werkzeug.security import generate_password_hash
from app import app
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
db = SQLAlchemy(app)

class User(db.Model):
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)  
    role = db.Column(db.String(20), nullable=False)
    is_flag = db.Column(db.Boolean,default=False)  

    
    sponsor = db.relationship("Sponsor", uselist=False, backref="user", cascade="all, delete-orphan")
    influencer = db.relationship("Influencer", uselist=False, backref="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f'<User {self.username}>'

class Sponsor(db.Model):
    
    id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    company_name = db.Column(db.String(100), nullable=False)
    industry = db.Column(db.String(50))
    budget = db.Column(db.Integer)
    is_flag = db.Column(db.Boolean,default=False)

    
    campaigns = db.relationship('Campaign', backref='sponsor', lazy=True)
   

class Influencer(db.Model):
    
    id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50))
    niche = db.Column(db.String(50))
    reach = db.Column(db.Integer)
    is_flag = db.Column(db.Boolean,default=False)
    Rating = db.Column(db.Integer)
    profile_picture = db.Column(db.String(100))
    
    

class Campaign(db.Model):
    
    id = db.Column(db.Integer, primary_key=True)
    sponsor_id = db.Column(db.Integer, db.ForeignKey('sponsor.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    niche = db.Column(db.Text)
    start_date = db.Column(db.Date)  
    end_date = db.Column(db.Date)
    budget = db.Column(db.Integer)
    is_flag = db.Column(db.Boolean, default=False)
    visibility = db.Column(db.String(10), default='public') 
    goals = db.Column(db.Text)
    
    
    ad_requests = db.relationship('AdRequest', backref='campaign', lazy=True)

class AdRequest(db.Model):
    
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'), nullable=False)
    sponsor_id = db.Column(db.Integer, db.ForeignKey('sponsor.id'))
    influencer_id = db.Column(db.Integer, db.ForeignKey('influencer.id'), nullable=False)
    by_sponsor = db.Column(db.Boolean, default=False) 
    ad_name = db.Column(db.Text)
    terms = db.Column(db.Text)
    description = db.Column(db.Text)
    payment_amount = db.Column(db.Integer)
    status = db.Column(db.String(10), default='pending')  

    sponsor = db.relationship('Sponsor', backref='ad_requests_sent', lazy=True, overlaps="ad_requests")
    influencer = db.relationship('Influencer', backref='ad_requests_received', lazy=True, overlaps="ad_requests")

with app.app_context():
    db.create_all()
    admin = User.query.filter_by(role='admin').first()

    if not admin:
        password_hash = generate_password_hash('admin')     
        admin = User(
            username='admin', 
            password=password_hash,
            role='admin' 
        )
        db.session.add(admin)
        db.session.commit()

