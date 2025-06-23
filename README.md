# Club Management System

A **web-based Club Management System** developed as a final-year Computer Science project at **Strathmore University**.

This platform simplifies the management of student clubs, event planning, member engagement, feedback, and administrative oversight through a centralized portal.

---

## 🔍 Features

- Student, Club Leader, and Admin roles with role-based access
- Club creation request and approval workflow
- Event scheduling and registration
- Membership management (join/exit)
- Notifications and email alerts
- Feedback submission
- Admin reporting and oversight dashboards
- M-PESA payment integration (planned)

---

## 🛠 Tech Stack

- **Backend**: Python, Flask, SQLAlchemy
- **Frontend**: HTML, CSS, JavaScript, Jinja2
- **Database**: MySQL
- **Tools**: Figma, Postman, Git, Draw.io

---

## ⚙️ Getting Started

### 🔧 Prerequisites

- Python 3.10+
- MySQL Server
- pip
- Git

### 📦 Installation

```bash
# Clone the repository
git clone https://github.com/your-username/Club-Management-System.git

# Navigate to project directory
cd Club-Management-System

# Create a virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create your .env file and configure DB and secret key
cp .env.example .env

# Run the application
flask run



