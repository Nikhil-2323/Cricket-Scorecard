🏏 Cricket Scorecard Web App (Flask)

A fully interactive Cricket Scorecard Web Application built using Flask, HTML, CSS, and JavaScript.
Update every ball manually and the app will automatically generate a complete cricket scoreboard with advanced features like bowler selection, wicket reasons, venue-based win probability, predicted scores, free-hit logic, extras handling, and more.

📛 Badges
<p> <img src="https://img.shields.io/badge/Python-3.10%2B-blue" /> <img src="https://img.shields.io/badge/Flask-Web%20Framework-green" /> <img src="https://img.shields.io/badge/Status-Active-success" /> <img src="https://img.shields.io/badge/License-MIT-yellow" /> <img src="https://img.shields.io/badge/Contributions-Welcome-brightgreen" /> </p>
📂 Project Structure
CRICKET SCORECARD/
│
├── app.py
├── scorecard.py
│
├── templates/
│   └── index.html
│
├── static/
│   ├── style.css
│   └── script.js
│
└── README.md

✨ Features
🏏 Ball-by-Ball Score Updating

Enter any ball: 0, 1, 2, 3, 4, 6, W, NB, WD, LB, BY

Extra runs after Wide or No-ball

Free Hit logic: No wicket allowed on next ball after a NB

🎯 Advanced Match Features

Select next bowler automatically after every over

Ask wicket reason (Caught, Bowled, LBW, Run Out, etc.)

Fall of wickets shows:

Batter name

Bowler name

Reason of dismissal

📊 Predictions & Stats

Predicted score using:

Current Run Rate (CRR)

CRR + 2

CRR + 4

Track remaining overs (Example: 1.3 completed → 18.3 remaining)

Track fours & sixes per batsman

🏟 Venue & Win Probability

Ask for venue name

Ask:

Matches won batting first

Matches won batting second

App calculates win probability based on history

🎨 Frontend UI Features

Full scorecard displayed cleanly

Highlights:

4s: Green

6s: Blue

Wickets: Red

Separate:

Current batting players

Out players

Displays the complete current over:
[1, 0, 4, W, WD, 6]

🚀 How to Run the Project
1️⃣ Install Flask
pip install flask

2️⃣ Run the Application
python app.py

3️⃣ Open in Browser
http://127.0.0.1:5000

🛠 Technologies Used

Python 3

Flask

HTML5

CSS3

JavaScript

Jinja2 Templates

📸 Screenshots 

![Home Page]<img width="1647" height="982" alt="Screenshot 2025-11-16 172524" src="https://github.com/user-attachments/assets/f37b3e99-b575-4167-a303-f5b06f15f2f9" />

![Scorecard]<img width="1627" height="975" alt="Screenshot 2025-11-16 172549" src="https://github.com/user-attachments/assets/0b607e9f-b61f-48c0-bef4-43f97a787189" />


🤝 Contribution Guidelines
How to Contribute

Fork this repository

Create a new feature branch

Commit your changes

Push to your branch

Open a Pull Request

Coding Style

Use meaningful variable names

Write modular & understandable code

Add comments when needed

📝 Commit Message Guidelines
feat: added bowler selection feature  
fix: corrected wicket logic  
ui: improved highlighting for boundaries  
refactor: optimized score update function  
docs: updated README  
