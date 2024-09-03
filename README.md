Influencer-Sponsor Coordination Platform
This platform streamlines the process of connecting influencers with sponsors for mutually beneficial collaborations.

Features
User Roles:

Sponsors: Create and manage campaigns, search and filter influencers, send and manage ad requests.
Influencers: Search for campaigns, manage ad requests (accept, reject, negotiate), edit profiles with picture uploads.
Admins: Oversee users, campaigns, and platform activity through an admin dashboard.
Campaign Management:

Sponsors can create, edit, and delete campaigns.
Campaigns have customizable details like niche, budget, and visibility (public or private).
Influencer Search:

Sponsors can search and filter influencers based on niche, reach, and name/username.
Influencers can search and filter public campaigns.
Ad Requests:

Sponsors and influencers can initiate ad requests.
Influencers can negotiate payment amounts.
Both parties can accept or reject ad requests.
Profile Management:

Users can view and edit their profiles.
Influencers can upload profile pictures.
Admin Control:

Admins can manage users, campaigns, and ad requests.
Admins have access to statistics and can flag/unflag users and campaigns.
Background Jobs:

Daily reminders to influencers about pending ad requests or new campaigns.
Monthly activity reports for sponsors.
CSV Export:

Sponsors can export campaign data in CSV format.
Technology Stack
Frontend: Vue.js, Bootstrap
Backend: Flask, SQLAlchemy
Database: SQLite
Caching: Redis
Background Tasks: Celery
Other: Werkzeug (password hashing, file uploads)
Installation
Clone the repository:

Bash
git clone https://github.com/gitnikhil18/AppDev-1.git
Use code with caution.

Navigate to the backend directory:

Bash
cd backend
Use code with caution.

Create and activate a virtual environment:

Bash
python -m venv venv
source venv/bin/activate  # On macOS/Linux
venv\Scripts\activate   
      # On Windows
Use code with caution.

Install dependencies:

Bash
pip install -r requirements.txt
Use code with caution.

Set up the database:

Bash
flask db init
flask db migrate
flask db upgrade   

Use code with caution.

Navigate to the frontend directory:

Bash
cd ../frontend
Use code with caution.

Install frontend dependencies:

Bash
npm install
Use code with caution.

Build the frontend:

Bash
npm run build
Use code with caution.

Copy the frontend build to the backend:

Copy the contents of the frontend/dist folder into the backend/templates folder.
Run the Flask development server:

Bash
cd ../backend
flask run
Use code with caution.

Access the application: Open your web browser and go to http://localhost:5000.
