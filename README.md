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

```bash
git clone https://github.com/Euene-misiko/Product-workflow-system.git
cd printflow


  


