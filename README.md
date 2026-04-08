### PrintFlow – Multi-Tenant Print Management System

- PrintFlow is a multi-tenant print management platform built with Django (DRF) and React (Vite).  
- It enables organizations to manage print orders efficiently from creation to delivery while maintaining strict role-based access and tenant isolation.

The platform is designed for scalability, allowing multiple companies to operate independently within the same system.

---

## System Architecture

PrintFlow follows a multi-tenant architecture:

### Platform Admin
- Manages the entire system  
- Invites and manages company admins  
- Oversees platform-wide operations  

### Company Admin
- Manages a specific company (tenant)  
- Invites and manages users within their company  
- Oversees orders, payments, and workflows  

### Company Users
- **Client** – Places orders, uploads designs, makes payments  
- **Designer** – Handles design tasks and updates statuses  
- **Printer** – Manages production and printing processes  

---

## Key Features

### Authentication & Authorization
- Custom user model with role-based access control  
- JWT-based authentication  
- Secure login and registration  
- Password reset and change functionality  
- Role-based access and route protection  

### Multi-Tenant Management
- Platform-level control of companies  
- Company-level isolation of data  
- Invitation-based onboarding system  
- Secure role assignment per tenant  

### Order Management
- Create and manage print orders  
- Add multiple items per order  
- Track order lifecycle:  
  **Pending → Confirmed → In Production → Delivered**  

### Design Management
- Upload and manage design files  
- Designers access assigned tasks  
- Design status updates  
- Secure file handling  

### Payments
- Payment submission by clients  
- Admin confirmation of payments  
- Order-based payment tracking  

### Notifications
- Real-time system notifications  
- User-specific notification feeds  
- Mark notifications as read  

### Delivery & Documentation
- Delivery tracking system  
- Upload and store legal/order documents  

### Admin Dashboard
- System overview and analytics  
- Orders and payments summary  
- Tenant-level insights  

---

## Frontend Features
- Built with React (JSX) and Vite  
- API integration using Axios  
- State management with Redux Toolkit  
- Protected routes and role-based UI  
- Dynamic dashboards per user role  
- Form validation and error handling  

---

## Technologies Used

### Backend
- Python 3  
- Django  
- Django REST Framework (DRF)  
- Simple JWT  

### Frontend
- React (JSX)  
- Vite  
- Axios  
- Redux Toolkit  

---

## Getting Started

### Prerequisites
Make sure you have installed:
- Python 3.8+  
- Node.js (v16+)  
- npm or yarn  

---

## Clone the Repository

git clone https://github.com/Eugene-misiko/Product-workflow-system.git
cd printflow

## Backend Setup (Django)

cd backend

python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate

pip install -r requirements.txt

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver

## Frontend Setup (React)

cd frontend

npm install
npm run dev

## Environment Variables

Create a `.env` file in both backend and frontend directories.

**Backend Example:**
``env
SECRET_KEY=your_secret_key
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost

**Frontend Example:**
``env
VITE_API_BASE_URL=http://127.0.0.1:8000/api
  
**Backend Setup**
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start server
python manage.py runserver

**Frontend Setup**
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev

***How the Invitation System Works**
#Platform Admin invites Company Admin
#Company Admin invites:
Clients
Designers
Printers
Invitations are sent via email with secure onboarding links
Users complete account setup and are assigned roles automatically
Project Structure
printflow/
│
├── backend/
├── frontend/
├── apps/
└── README.md
---

**Contributing**
We welcome contributions to improve PrintFlow 

**Steps to Contribute**
Fork the repository
Create a new branch
git checkout -b feature/your-feature-name

Make your changes
Commit your changes:
git commit -m "Add: your feature description"
Push to your branch:
git push origin feature/your-future-name

Open a Pull Request
Contribution Guidelines
Follow clean code practices
Write meaningful commit messages
Ensure code is tested before submitting
Keep UI/UX consistent
Security Notes
Ensure proper tenant isolation
Do not expose admin routes to unauthorized users
Always validate user roles on backend
Use HTTPS in production
Contact & Support
For support, questions, or collaboration:

 Phone: 0742193774
 Email: eugenemisiko438@gmail.com

***License**
-This project is licensed under the MIT License.
