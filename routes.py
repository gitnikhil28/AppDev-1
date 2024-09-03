from app import app
from flask import render_template, request, redirect, session, url_for, flash
from models import db,User,Influencer,Sponsor, Campaign, AdRequest
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
import io
import seaborn as sns
import io
import os
from werkzeug.utils import secure_filename

def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if 'username' not in session:
            flash("You need to login first")
            return redirect(url_for('login'))
        user = User.query.filter_by(username=session['username']).first()
        if not user:
            session.pop('username')
            return redirect(url_for('login'))
        if not user.is_admin:
            flash("You are not authorized to visit this page")
            return redirect(url_for('login'))
        return func(*args, **kwargs)
    return wrapper





def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'user_id' not in session:
            flash("You need to login first")
            return redirect(url_for('login'))
        else:
            user_id  = session['user_id']
            user = User.query.filter_by(id=user_id).first()

            if user.is_flag:
                flash("You are flagged")
                return redirect(url_for('login'))


        
            
        return f(*args, **kwargs)
    
    return wrap

@app.route("/")
def login():
    
    return render_template('login.html')


@app.route("/",methods=['GET', 'POST'])
def login_post():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):  
            session['user_id'] = user.id
            session['role'] = user.role
            if user.role == "sponsor":
                flash('Logged in successfully', "success")
                return redirect(url_for('sponsor_profile', user_id=user.id))
            elif user.role == "influencer":
                flash('Logged in successfully', "success")
                return redirect(url_for('influencer_profile', user_id=user.id))
            elif user.role == "admin":  # Check for admin role
                flash('Logged in successfully', "success")
                return redirect(url_for('admin_users', user_id=user.id))
        else:
            flash('Invalid username or password', "danger")

    return render_template('login.html')

@app.route("/sponsor/registration",methods=['GET', 'POST'])
def spnreg():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        repassword = request.form['repassword']
        name = request.form.get('name')
        industry = request.form.get('industry')
        


        if password != repassword:
            flash('Passwords do not match')
            return redirect(url_for('spnreg'))
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already taken')
            return redirect(url_for('spnreg'))
        
        passhash=generate_password_hash(password)
        new_user = User(username=username, password=passhash, role='sponsor')
        db.session.add(new_user)
        db.session.flush()
        new_sponsor = Sponsor(
            id=new_user.id,  # Link to the new user
            company_name=name,
            industry=industry,
            # ... other sponsor fields
        )
        db.session.add(new_sponsor)
        db.session.commit()

        return redirect(url_for('tqre'))
    return render_template('spnreg.html')

NICHE_OPTIONS = [
    "Fashion & Beauty",
    "Lifestyle",
    "Travel ",
    "Fitness & Health",
    "Gaming",
    "Food & Cooking",
    "Technology",
    "Finance",
    "Entertainment"
]


@app.route("/influencer/registration",methods=['GET', 'POST'])
def infreg():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        repassword = request.form['repassword']
        niche = request.form['niche']
        reach = int(request.form['reach'])
        name = request.form['name']
        

        if password != repassword:
            flash('Passwords do not match',"danger")
            return redirect(url_for('spnreg'))
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already taken',"danger")
            return redirect(url_for('infreg'))
        
        passhash=generate_password_hash(password)
        new_user = User(username=username, password=passhash, role='influencer')
        db.session.add(new_user)
        db.session.flush()

        new_influencer = Influencer(
            id=new_user.id,
            name=name,
            niche=niche,
            reach=reach
        )
        db.session.add(new_influencer)
        db.session.commit()
        return redirect(url_for('tqre'))


    return render_template('infreg.html', niche_options=NICHE_OPTIONS)

@app.route("/registration/success")
def tqre():
    return render_template('tqreg.html')

@app.route("/sponsor/dashboard")
@login_required
def spndash():
    user_id = session.get('user_id')
    sponsor = Sponsor.query.get(user_id) 

    if not sponsor:
        flash("You are not authorized to view this page", "danger")
        return redirect(url_for('login'))

    return render_template('spndash.html', sponsor=sponsor)

@app.route("/influencer/dashboard")
@login_required
def infdash():
    user_id = session.get('user_id')
    influencer = Influencer.query.get(user_id)

    if not influencer:
        flash("You are not authorized to view this page", "danger")
        return redirect(url_for('login'))

    return render_template('ifndash.html', influencer=influencer)

@app.route("/logout")
def logout():
    
    flash('Logged out successfully',"success")
    
    session.pop('user_id',None)
    # Redirect to the home page
    return redirect(url_for('login'))

@app.route("/sponsor/profile", methods=['GET','POST'])
@login_required
def sponsor_profile():
    user_id = session.get('user_id')
    sponsor = Sponsor.query.get(user_id)
    if not sponsor:
        flash("You are not authorized to view this page", "danger")
        return redirect(url_for('login'))

    campaigns = sponsor.campaigns 
    # Fetching ad requests created by influencers for the sponsor's campaigns
    ad_requests = AdRequest.query.filter_by(sponsor_id=sponsor.id, by_sponsor=False,status='pending').all() 

    return render_template(
        'spn_profile.html',
        sponsor=sponsor, 
        campaigns=campaigns, 
        ad_requests=ad_requests,  
        campaign_progress=campaign_progress
    )




@app.route("/sponsors/create_campaign", methods=['GET','POST'])
@login_required
def create_campaign():
    user_id = session.get('user_id')
    sponsor = Sponsor.query.get(user_id)

    if sponsor.is_flag:  # Check if sponsor is flagged
        flash("You are not allowed to create campaigns.", "danger")
        return redirect(url_for('sponsor_profile'))
    
    if request.method == 'POST':
        
        
        title = request.form['title']
        description = request.form['description']
        visibility = request.form['visibility']
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        budget = request.form['budget']
        niche = request.form['niche']

        print(user_id)

        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

        new_campaign = Campaign(sponsor_id=sponsor.id, name=title, description=description
                                ,visibility=visibility, 
                                start_date=start_date, end_date=end_date, budget=budget,niche=niche)
        
        db.session.add(new_campaign)
        db.session.commit()

        flash('Campaign created successfully',"success")
        return redirect(url_for('sponsor_profile'))
    return render_template('create_campaign.html', niche_options=NICHE_OPTIONS)


@app.route("/sponsor/campaigns")
@login_required
def spncamp():
    user_id = session.get('user_id')
    sponsor = Sponsor.query.get(user_id)
    if not sponsor:
        flash("You are not authorized to view this page", "danger")
        return redirect(url_for('login'))

    campaigns = sponsor.campaigns  # Access campaigns directly through the relationship
    return render_template('spn_campaigns.html', sponsor=sponsor, campaigns=campaigns,campaign_progress=campaign_progress)


@app.route("/sponsor/edit_campaign/<int:campaign_id>", methods=['GET','POST'])
@login_required
def edit_campaign(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    user_id = session.get('user_id')
    if user_id != campaign.sponsor.user.id:
        flash("You are not authorized to edit this campaign", "danger")
        return redirect(url_for('spncamp'))

    return render_template("edit_campaign.html", campaign=campaign)

@app.route("/sponsor/update_campaign/<int:campaign_id>", methods=['POST'])
@login_required
def update_campaign_sponsor(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    user_id = session.get('user_id')
    if user_id != campaign.sponsor.user.id:
        flash("You are not authorized to edit this campaign", "danger")
        return redirect(url_for('spncamp'))

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        niche = request.form['niche']
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        budget = request.form['budget']
        visibility = request.form['visibility']

        # Input validation (add more checks as needed)
        if not title or not description or not start_date or not end_date or not budget:
            flash("All fields are required.", "danger")
            return redirect(url_for('edit_campaign', campaign_id=campaign_id))

        
            
        campaign.name = title
        campaign.description = description
        campaign.niche = niche
        campaign.start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        campaign.end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        campaign.budget = int(budget)  # Convert budget to integer
        campaign.visibility = visibility

        db.session.commit()
        flash('Campaign updated successfully.', 'success')
        return redirect(url_for('sponsor_profile', user_id=user_id))
        

    return redirect(url_for('edit_campaign', campaign_id=campaign_id))

@app.route("/sponsor/edit_ad_request/<int:ad_request_id>", methods=['GET', 'POST'])
@login_required
def edit_ad_request(ad_request_id):
    user_id = session.get('user_id')
    ad_request = AdRequest.query.get_or_404(ad_request_id)
    influencers = Influencer.query.all()

    # Authorization check (ensure the current user owns the ad request)
    if user_id != ad_request.sponsor_id:
        flash("You are not authorized to edit this ad request", "danger")
        return redirect(url_for('spncamp'))

    if request.method == 'POST':
        # Update ad request details (add your update logic here)
        pass

    return render_template("edit_ad_request.html", ad_request=ad_request, influencers=influencers)
    
    if user_id != ad_request.sponsor_id:
        flash("You are not authorized to edit this ad request", "danger")
        return redirect(url_for('spncamp'))

    if request.method == 'POST':
        # Update ad request details (add your update logic here)
        pass
    
    # Fetch associated influencer
    

    return render_template("edit_ad_request.html", ad_request=ad_request, influencers=influencers)

@app.route("/sponsor/update_ad_request/<int:ad_request_id>", methods=['POST'])
@login_required
def update_ad_request(ad_request_id):
    ad_request = AdRequest.query.get_or_404(ad_request_id)
    user_id = session.get('user_id')

    if request.method == "POST":
        ad_name = request.form.get("ad_name")
        description = request.form.get("description")
        terms = request.form.get("requirements")  # Assuming 'requirements' is the correct field name in the form
        payment_amount = request.form.get("payment_amount")
        influencer_id = request.form.get("influencer_id")
        if influencer_id and \
           (not ad_request.by_sponsor or ad_request.status == 'pending'):
            ad_request.influencer_id = int(influencer_id) 


        
        if ad_name:
            ad_request.ad_name = ad_name
        if description:
            ad_request.description = description
        if terms:
            ad_request.terms = terms
        if payment_amount:
            ad_request.payment_amount = int(payment_amount)  # Convert to integer if needed
        if influencer_id:
            ad_request.influencer_id = int(influencer_id) 

        if ad_request.by_sponsor: 
            ad_request.status = request.form.get("status")

        
        db.session.commit()
        flash('Ad Request updated successfully.', 'success')
        return redirect(url_for('sponsor_ad_requests', campaign_id=ad_request.campaign_id))
        
            

    return redirect(url_for('edit_ad_request', ad_request_id=ad_request_id))


@app.route("/sponsor/delete_ad_request/<int:ad_request_id>", methods=["POST"])
@login_required
def delete_ad_request_sponsor(ad_request_id):
    ad_request = AdRequest.query.get_or_404(ad_request_id)
    user_id = session.get('user_id')

    # Authorization check (ensure the sponsor owns the ad request or it's pending)
    if user_id != ad_request.sponsor_id:
        flash("You are not authorized to delete this ad request", "danger")
        return redirect(url_for('sponsor_ad_requests'))  # Redirect to the sponsor's ad requests page

    try:
        db.session.delete(ad_request)
        db.session.commit()
        flash("Ad request deleted successfully.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting ad request: {e}", "danger")

    return redirect(url_for('sponsor_ad_requests')) 


@app.route("/sponsor/delete_campaign/<int:campaign_id>", methods=["POST"])
@login_required
def delete_campaign_sponsor(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    user_id = session.get('user_id')
    if user_id != campaign.sponsor.user.id:
        flash("You are not authorized to delete this campaign", "danger")
        return redirect(url_for('spncamp'))


    try:
        # Delete associated AdRequests before deleting the Campaign
        for ad_request in campaign.ad_requests:
            db.session.delete(ad_request)

        db.session.delete(campaign)
        db.session.commit()

        flash("Campaign deleted successfully.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting campaign: {e}", "danger")

    return redirect(url_for('sponsor_profile'))

@app.route("/sponsor/campaigns/<int:campaign_id>")
@login_required
def campaign_details(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)  # Get campaign or 404
    return render_template('campaign_details.html', campaign=campaign)



@app.route("/sponsor/create_ad_request/<int:campaign_id>", methods=['GET', 'POST'])
@login_required
def create_ad_request(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    user_id = session.get('user_id')
    sponsor = Sponsor.query.get(user_id)

    if campaign.is_flag:  # Check if campaign is flagged
        flash("You cannot create ad requests for a flagged campaign.", "danger")
        return redirect(url_for('campaign_details', campaign_id=campaign_id))

    influencer_id = request.args.get('influencer_id') 
    if influencer_id:
        influencer = Influencer.query.get(influencer_id)
        influencer_username = influencer.user.username if influencer else None
    else:
        influencer_username = None
    if request.method == 'POST':
        ad_name = request.form['ad_name']
        description = request.form['description']
        terms = request.form['terms']
        payment_amount = request.form['payment_amount']
        influencer_id = request.form['influencer_id']
        
        influencer = Influencer.query.get(influencer_id)
        if not influencer:
            flash('Influencer not found', "danger")
            return redirect(url_for('create_ad_request', campaign_id=campaign_id))

        new_ad_request = AdRequest(
            ad_name=ad_name,
            description=description,
            campaign_id=campaign_id,
            influencer_id=influencer.id,
            sponsor_id=sponsor.id,
            by_sponsor=True,
            terms=terms,
            payment_amount=payment_amount,
            status='pending'
        )

        db.session.add(new_ad_request)
        db.session.commit()

        flash('Ad request created successfully', "success")
        return redirect(url_for('campaign_details', campaign_id=campaign_id))

    return render_template('ad_request.html', campaign=campaign, influencer_username=influencer_username, influencer_id=influencer_id)

@app.route("/sponsor/ad_request/<int:ad_request_id>")
@login_required
def view_ad_request(ad_request_id):
    ad_request = AdRequest.query.get_or_404(ad_request_id)
    return render_template("ad_request_details.html", ad_request=ad_request)

@app.route("/sponsor/handle_ad_request/<int:ad_request_id>", methods=['POST'])
@login_required
def handle_ad_request(ad_request_id):
    ad_request = AdRequest.query.get_or_404(ad_request_id)
    action = request.form.get('action')

    if action == 'accept':
        ad_request.status = 'accepted'
    elif action == 'reject':
        ad_request.status = 'rejected'
    else:
        flash('Invalid action.', 'danger')

    db.session.commit()
    return redirect(url_for('sponsor_profile'))

@app.route('/search_influencers', methods=['GET', 'POST'])
@login_required
def search_influencers():
    campaign_id = request.args.get('campaign_id')
    campaign = Campaign.query.get(campaign_id)

    selected_niche = request.form.get('niche', 'none')

    if selected_niche == 'none':
        influencers = Influencer.query.all()
    else:
        influencers = Influencer.query.filter_by(niche=selected_niche).all()

    niches = db.session.query(Influencer.niche.distinct()).all()
    niches = [niche[0] for niche in niches]

    return render_template('search_influencers.html', campaign=campaign, influencers=influencers, niches=niches, selected_niche=selected_niche)

@app.route('/sponsor/ad_requests')
@login_required
def sponsor_ad_requests():
    user_id = session.get('user_id')
    sponsor = Sponsor.query.get(user_id)

    # Fetch all ad requests related to the sponsor (both sent and received)
    all_ad_requests = AdRequest.query.filter(
        (AdRequest.sponsor_id == sponsor.id)
    ).all()

    return render_template('sponsor_ad_requests.html', sponsor=sponsor, ad_requests=all_ad_requests)


@app.route("/influencer/profile", methods=['GET', 'POST'])
@login_required
def influencer_profile():
    user_id = session.get('user_id')
    influencer = Influencer.query.get(user_id)

    if not influencer:
        flash("You are not authorized to view this page", "danger")
        return redirect(url_for('login'))

    # active_campaigns = []
    # for ad_request in influencer.ad_requests_received:
    #     if ad_request.status == "accepted" and ad_request.campaign.start_date <= datetime.now().date() <= ad_request.campaign.end_date:
    #         active_campaigns.append(ad_request.campaign)

    active_campaigns = (
        db.session.query(Campaign)  
        .join(AdRequest)
        .filter(
            AdRequest.influencer_id == influencer.id,
            AdRequest.status == 'accepted',
            Campaign.start_date <= datetime.now(),
            Campaign.end_date >= datetime.now()
        )
        .distinct(Campaign.id)   # Ensure only unique campaigns are returned
        .all()
    )

    new_ad_requests = AdRequest.query.filter_by(influencer_id=influencer.id, by_sponsor=1,status='pending').all() 

    total_earnings = sum([request.payment_amount for request in influencer.ad_requests_received if request.status == 'accepted'])

    return render_template(
        'inf_profile.html', 
        influencer=influencer,
        active_campaigns=active_campaigns, 
        new_ad_requests=new_ad_requests,
        total_earnings=total_earnings,
        campaign_progress=campaign_progress

    )
UPLOAD_FOLDER = 'static/uploads'   # Path to the uploads folder
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS




@app.route('/influencer/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_influencer_profile():
    user_id = session.get('user_id')
    influencer = Influencer.query.get(user_id)

    if request.method == 'POST':
        # Update influencer details from the form
        influencer.name = request.form['name']
        influencer.niche = request.form['niche']
        influencer.reach = int(request.form['reach'])
        # ... update other fields as needed
        if 'profile_picture' in request.files:
            file = request.files['profile_picture']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                influencer.profile_picture = filename

        try:
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('influencer_profile'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while updating your profile.', 'danger')

    return render_template('edit_influencer_profile.html', influencer=influencer, niche_options=NICHE_OPTIONS)

@app.route('/influencer/ad_requests')
@login_required
def influencer_ad_requests():
    user_id = session.get('user_id')
    influencer = Influencer.query.get(user_id)

    # Fetch all ad requests related to the influencer (both sent and received)
    all_ad_requests = AdRequest.query.filter(
        (AdRequest.influencer_id == influencer.id) | 
        (AdRequest.sponsor_id == influencer.id)
    ).all()

    return render_template('influencer_ad_requests.html', influencer=influencer, ad_requests=all_ad_requests)

@app.route("/influencer/delete_ad_request/<int:ad_request_id>", methods=["POST"])
@login_required
def delete_ad_request_influencer(ad_request_id):
    ad_request = AdRequest.query.get_or_404(ad_request_id)
    user_id = session.get('user_id')

    if user_id != ad_request.influencer_id or ad_request.by_sponsor:  # Ensure influencer owns the request and it's not sent by sponsor
        flash("You are not authorized to delete this ad request", "danger")
        return redirect(url_for('influencer_ad_requests')) 

    try:
        db.session.delete(ad_request)
        db.session.commit()
        flash("Ad request deleted successfully.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting ad request: {e}", "danger")

    return redirect(url_for('influencer_ad_requests',ad_request_id= ad_request.id)) 

@app.route('/influencer/stats')
@login_required
def influencer_stats():
    user_id = session.get('user_id')
    influencer = Influencer.query.get(user_id)

    # Calculate total earnings
    total_earnings = sum(
        [request.payment_amount for request in influencer.ad_requests_received if request.status == 'accepted']
    )

    # Count active campaigns
    active_campaigns_count = (
        db.session.query(Campaign)
        .join(AdRequest)
        .filter(
            AdRequest.influencer_id == influencer.id,
            AdRequest.status == 'accepted',
            Campaign.start_date <= datetime.now(),
            Campaign.end_date >= datetime.now()
        )
        .count()
    )

    # Data for earnings chart 
    campaign_names = []
    campaign_earnings = []
    for ad_request in influencer.ad_requests_received:
        if ad_request.status == 'accepted':
            campaign_names.append(ad_request.campaign.name)
            campaign_earnings.append(ad_request.payment_amount)

    # Data for ad request status chart
    ad_request_status_counts = [
    db.session.query(AdRequest).filter_by(influencer_id=influencer.id, status='pending').count(),
    db.session.query(AdRequest).filter_by(influencer_id=influencer.id, status='accepted').count(),
    db.session.query(AdRequest).filter_by(influencer_id=influencer.id, status='rejected').count()
]

    return render_template(
        'influencer_stats.html',
        total_earnings=total_earnings,
        active_campaigns_count=active_campaigns_count,
        campaign_names=campaign_names,
        campaign_earnings=campaign_earnings,
        ad_request_status_counts=ad_request_status_counts
    )

@app.route('/sponsor/stats')
@login_required
def sponsor_stats():
    user_id = session.get('user_id')
    sponsor = Sponsor.query.get(user_id)
    
    # Fetch relevant data
    
    campaigns = Campaign.query.filter_by(sponsor_id=sponsor.id).all()
    
    total_amount_spent = sum([campaign.budget for campaign in campaigns])
    total_reach = sum([sum(ad.influencer.reach for ad in campaign.ad_requests) for campaign in campaigns])

    # Prepare data for charts
    campaign_names = [campaign.name for campaign in campaigns]
    campaign_budgets = [campaign.budget for campaign in campaigns]
    ad_requests_counts = [len(campaign.ad_requests) for campaign in campaigns]
    campaign_reaches = [sum(ad.influencer.reach for ad in campaign.ad_requests) for campaign in campaigns]

    return render_template('sponsor_stats.html', 
                           campaign_names=campaign_names,
                           campaign_budgets=campaign_budgets,
                           ad_requests_counts=ad_requests_counts,
                           campaign_reaches=campaign_reaches,
                           total_amount_spent=total_amount_spent, 
                           total_reach=total_reach,
                           sponsor=sponsor)

@app.route('/search_influencers_for_campaign/<int:campaign_id>', methods=['GET'])
@login_required
def search_influencers_for_campaign(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)

    search_query = request.args.get('search', '')
    selected_niche = request.args.get('niche', '')
    min_reach = request.args.get('min_reach', 0, type=int)

    query = Influencer.query.join(User).filter(Influencer.is_flag == False)

    if search_query:
        query = query.filter(
            Influencer.name.ilike(f'%{search_query}%') |
            User.username.ilike(f'%{search_query}%')
        )

    if min_reach > 0:
        query = query.filter(Influencer.reach >= min_reach)

    if selected_niche:
        query = query.filter(Influencer.niche == selected_niche) 

    influencers = query.all()

    
    niches = db.session.query(Influencer.niche.distinct()).all()
    niches = [niche[0] for niche in niches]

    return render_template('search_influencers_for_campaign.html',
                           campaign=campaign, influencers=influencers, niches=niches)

@app.route("/influencer/ad_request/<int:ad_request_id>")
@login_required
def view_ad_request_inf(ad_request_id):
    ad_request = AdRequest.query.get_or_404(ad_request_id)
    return render_template("ad_request_influencer.html", ad_request=ad_request)


@app.route("/influencer/handle_ad_request/<int:ad_request_id>", methods=['POST'])
@login_required
def handle_ad_request_inf(ad_request_id):
    ad_request = AdRequest.query.get_or_404(ad_request_id)
    action = request.form.get('action')

    if action == 'accept':
        ad_request.status = 'accepted'
    elif action == 'reject':
        ad_request.status = 'rejected'
    else:
        flash('Invalid action.', 'danger')

    db.session.commit()
    return redirect(url_for('view_ad_request_inf'))  

def campaign_progress(campaign):
    start_date = campaign.start_date 
    end_date = campaign.end_date     
    today = datetime.today().date() 

    if today < start_date:
        return 0  
    elif today > end_date:
        return 100  

    total_days = (end_date - start_date).days
    days_passed = (today - start_date).days
    progress = (days_passed / total_days) * 100
    return int(progress)

@app.route("/influencer/find")
@login_required
def inf_find():
    search_query = request.args.get('search', '')
    selected_niche = request.args.get('niche', '')

    query = Campaign.query.filter_by(visibility='public', is_flag=False)

    if search_query:
        query = query.filter(Campaign.name.ilike(f'%{search_query}%')) 

    if selected_niche:
        query = query.filter_by(niche=selected_niche)

    campaigns = query.all()

    # Get unique niches from all public campaigns
    niches = db.session.query(Campaign.niche.distinct()).filter_by(visibility='public', is_flag=False).all()
    niches = [niche[0] for niche in niches] 

    return render_template('inf_find.html', campaigns=campaigns, niches=niches)

@app.route("/influencer/find/<int:campaign_id>")
@login_required
def inf_campaign_details(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)  
    return render_template('inf_campaign_details.html', campaign=campaign)



@app.route("/influencer/create_ad_request/<int:campaign_id>", methods=['GET', 'POST'])
@login_required
def create_ad_request_influencer(campaign_id):
    user_id = session.get('user_id')
    influencer = Influencer.query.get(user_id)
    campaign = Campaign.query.get_or_404(campaign_id)

    if influencer.is_flag:
        
        flash('You are flagged, so cannot create ad requests', "success")
        return redirect(url_for('inf_find')) 

    if request.method == 'POST':
        ad_name = request.form['ad_name']
        description = request.form['description']
        terms = request.form['terms']
        payment_amount = request.form['payment_amount']

        # Create the new ad request object
        new_ad_request = AdRequest(
            campaign_id=campaign_id,
            influencer_id=influencer.id,
            sponsor_id=campaign.sponsor_id,
            ad_name=ad_name,  # Include ad_name
            description=description,
            terms=terms,
            payment_amount=payment_amount,
            status='pending',
            by_sponsor=False  # Influencer is sending the request
        )

        db.session.add(new_ad_request)
        db.session.commit()

        flash('Ad request created successfully', "success")
        return redirect(url_for('inf_find'))  
    return render_template('create_ad_request_influencer.html', campaign=campaign)

@app.route("/admin/dashboard")
@login_required
def admin_dashboard():
      
    return render_template('admin_dash.html')

@app.route("/admin/users")
@login_required
def admin_users():
    search_query = request.args.get('search', '')
    selected_role = request.args.get('role', '')

    query = User.query.filter(User.role != 'admin')  
    if search_query:
        query = query.filter(
            User.username.ilike(f'%{search_query}%') | 
            Sponsor.company_name.ilike(f'%{search_query}%') | 
            Influencer.name.ilike(f'%{search_query}%')
        ).outerjoin(Sponsor).outerjoin(Influencer) 

    if selected_role:
        query = query.filter_by(role=selected_role)

    users = query.all()
    return render_template('admin_users.html', users=users)

@app.route("/admin/flag_user/<int:user_id>", methods=["POST"])
@login_required
def flag_user(user_id):
    user = User.query.get_or_404(user_id)

    try:
        is_flagged = None  # Initialize is_flagged

        if user.role == 'sponsor':
            sponsor = Sponsor.query.get(user_id)
            if sponsor:
                sponsor.is_flag = not sponsor.is_flag  # Toggle flag for sponsor
                is_flagged = sponsor.is_flag
            else:
                flash("Sponsor not found.", "danger")
        elif user.role == 'influencer':
            influencer = Influencer.query.get(user_id)
            if influencer:
                influencer.is_flag = not influencer.is_flag  
                is_flagged = influencer.is_flag
            else:
                flash("Influencer not found.", "danger")
        else:
            flash("Invalid user role.", "danger")

        db.session.commit()

        if is_flagged is not None:  # Check if is_flagged was set
            flash(f"User {user.username} has been {'flagged' if is_flagged else 'unflagged'}.", "success")
        
    except Exception as e:
        db.session.rollback()
        flash(f"Error flagging/unflagging user: {e}", "danger")

    return redirect(url_for('admin_users'))

@app.route("/admin/users/<int:user_id>")
@login_required
def admin_user_details(user_id):
    
    user = User.query.get_or_404(user_id)  # Get campaign or 404
    return render_template('admin_user_details.html', user=user)


@app.route("/admin/campaigns")
@login_required
def admin_campaigns():
    search_query = request.args.get('search', '')
    selected_niche = request.args.get('niche', '')

    query = Campaign.query

    if search_query:
        query = query.filter(Campaign.name.ilike(f'%{search_query}%'))

    if selected_niche:
        query = query.filter_by(niche=selected_niche)

    campaigns = query.all()

    # Get unique niches from all campaigns
    niches = db.session.query(Campaign.niche.distinct()).all()
    niches = [niche[0] for niche in niches]

    return render_template('admin_campaigns.html', campaigns=campaigns, niches=niches)

@app.route("/admin/campaigns/<int:campaign_id>")  # Changed to GET only
@login_required
def admin_campaign_details(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    return render_template('admin_campaign_details.html', campaign=campaign)

@app.route("/admin/flag_campaign/<int:campaign_id>", methods=["POST"])
@login_required
def flag_campaign(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    is_flagged = campaign.is_flag # Check if the campaign is flagged or not

    try:
        campaign.is_flag = not campaign.is_flag  # Toggle the flag
        db.session.commit()

        if is_flagged is not None:  # Check if is_flagged was set
            flash(f"{campaign.name} has been {'unflagged' if is_flagged else 'flagged'}.", "success")
        
    except Exception as e:
        db.session.rollback()
        flash(f"Error flagging/unflagging campaign: {e}", "danger")

    return redirect(url_for('admin_campaigns'))


@app.route("/admin/add/sponsor",methods=['GET', 'POST'])
@login_required
def admin_creates():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        repassword = request.form['repassword']
        name = request.form.get('name')
        industry = request.form.get('industry')
        


        if password != repassword:
            flash('Passwords do not match')
            return redirect(url_for('spnreg'))
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already taken')
            return redirect(url_for('spnreg'))
        
        passhash=generate_password_hash(password)
        new_user = User(username=username, password=passhash, role='sponsor')
        db.session.add(new_user)
        db.session.flush()
        new_sponsor = Sponsor(
            id=new_user.id,  # Link to the new user
            company_name=name,
            industry=industry,
            # ... other sponsor fields
        )
        db.session.add(new_sponsor)
        db.session.commit()

        return redirect(url_for('admin_users'))
    
    
    return render_template('admin_creates.html')

@app.route("/admin/add/influencer",methods=['GET', 'POST'])
@login_required
def admin_create_inf():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        repassword = request.form['repassword']
        niche = request.form['niche']
        reach = int(request.form['reach'])
        name = request.form['name']


        if password != repassword:
            flash('Passwords do not match',"danger")
            return redirect(url_for('spnreg'))
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already taken',"danger")
            return redirect(url_for('infreg'))
        
        passhash=generate_password_hash(password)
        new_user = User(username=username, password=passhash, role='influencer')
        db.session.add(new_user)
        db.session.flush()

        new_influencer = Influencer(
            id=new_user.id,
            name=name,
            niche=niche,
            reach=reach
        )
        db.session.add(new_influencer)
        db.session.commit()
        return redirect(url_for('admin_users'))

    
    return render_template('admin_createinf.html')

@app.route("/admin/users/<int:user_id>/update", methods=["GET", "POST"])
@login_required
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    if request.method == "POST":
        user.username = request.form.get("username")
        
        # Update sponsor/influencer details based on user role
        if user.role == "sponsor":
            user.sponsor.company_name = request.form.get("company_name")
            user.sponsor.industry = request.form.get("industry")
        elif user.role == "influencer":
            user.influencer.name = request.form.get("name")
            user.influencer.niche = request.form.get("niche")
            user.influencer.reach = request.form.get("reach", type=int)
            user.influencer.Rating = request.form.get("rating", type=int)
        
        db.session.commit()
        flash("User updated successfully.", "success")
        return redirect(url_for('admin_users'))

    return render_template("admin_user_details.html", user=user)  # Re-render with potential errors



@app.route("/admin/users/<int:user_id>/delete", methods=["POST"])
@login_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)

    
    
    if user.role == 'sponsor':
        sponsor = Sponsor.query.get(user_id)
        if sponsor:
                # Delete associated campaigns
            for campaign in sponsor.campaigns:
             db.session.delete(campaign)
            
            for ad_request in sponsor.ad_requests_sent:
                    db.session.delete(ad_request)

    else:
        influencer = Influencer.query.get(user_id)
        if influencer:
                # Delete associated ad requests
            for ad_request in influencer.ad_requests_received:
             db.session.delete(ad_request)
            

    db.session.delete(user)
    db.session.commit()
    flash("User deleted successfully.", "success")
    
    

    return redirect(url_for('admin_users'))

@app.route("/admin/campaigns/<int:campaign_id>/update", methods=["GET", "POST"])
@login_required
def update_campaign(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    if request.method == "POST":
        campaign.name = request.form.get("name")
        campaign.description = request.form.get("description")
        campaign.niche = request.form.get("niche")
        campaign.start_date = datetime.strptime(request.form.get("start_date"), '%Y-%m-%d').date()
        campaign.end_date = datetime.strptime(request.form.get("end_date"), '%Y-%m-%d').date()
        campaign.budget = request.form.get("budget")
        campaign.visibility = request.form.get("visibility")
        campaign.goals = request.form.get("goals")

        db.session.commit()
        flash("Campaign updated successfully.", "success")
        return redirect(url_for('admin_campaigns'))

    return render_template("admin_campaign_details.html", campaign=campaign) 

@app.route("/admin/campaigns/<int:campaign_id>/delete", methods=["POST"])
@login_required
def delete_campaign(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    
    for ad_request in campaign.ad_requests:
        db.session.delete(ad_request)
    
    db.session.delete(campaign)
    db.session.commit()
    flash("Campaign deleted successfully.", "success")
    

    return redirect(url_for('admin_campaigns'))




@app.route('/admin_stats')
def admin_stats():
    total_users = User.query.count()
    total_influencers = Influencer.query.count()
    total_sponsors = Sponsor.query.count()

    active_influencers = Influencer.query.join(AdRequest).filter(AdRequest.status == 'accepted').distinct().count()
    active_sponsors = Sponsor.query.join(Campaign).filter(Campaign.end_date >= datetime.utcnow()).distinct().count()
    flagged_sponsors_count = Sponsor.query.filter_by(is_flag=1).count()
    flagged_influencers_count = Influencer.query.filter_by(is_flag=1).count()

    public_campaigns = Campaign.query.filter_by(visibility='public').count()
    private_campaigns = Campaign.query.filter_by(visibility='private').count()

    campaigns_by_niche = db.session.query(Campaign.niche, db.func.count(Campaign.id)).group_by(Campaign.niche).all()
    campaigns_by_niche = [(niche, count) for niche, count in campaigns_by_niche]

    pending_ad_requests = AdRequest.query.filter_by(status='pending').count()
    accepted_ad_requests = AdRequest.query.filter_by(status='accepted').count()
    rejected_ad_requests = AdRequest.query.filter_by(status='rejected').count()

    ad_requests_by_influencer = db.session.query(AdRequest.influencer_id, db.func.count(AdRequest.id)).group_by(AdRequest.influencer_id).all()
    ad_requests_by_influencer = [(influencer_id, count) for influencer_id, count in ad_requests_by_influencer]

    return render_template(
        'admin_stats.html',
        total_users=total_users,
        total_influencers=total_influencers,
        total_sponsors=total_sponsors,
        active_influencers=active_influencers,
        active_sponsors=active_sponsors,
        public_campaigns=public_campaigns,
        private_campaigns=private_campaigns,
        campaigns_by_niche=campaigns_by_niche,
        pending_ad_requests=pending_ad_requests,
        accepted_ad_requests=accepted_ad_requests,
        rejected_ad_requests=rejected_ad_requests,
        ad_requests_by_influencer=ad_requests_by_influencer,
        flagged_sponsors_count = flagged_sponsors_count,
        flagged_influencers_count = flagged_influencers_count
    )



if __name__ == '__main__':
    
    app.run(debug = True)