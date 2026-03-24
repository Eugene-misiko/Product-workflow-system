# Product-workflow-system
# PrintFlow

PrintFlow is a role-based print order management system built using **Django** and **Django REST Framework (DRF)**.  
It provides a complete backend solution with both **REST APIs** and **HTML-based interfaces**, allowing future frontend integration while remaining fully functional on its own.

---

## Project Description

PrintFlow is designed to manage print orders from creation to delivery.  
The system supports three user roles:

- **Client** – places orders, uploads designs, makes payments
- **Designer** – handles design requests and updates design status
- **Admin** – manages users, orders, payments, approvals, and system reports

The project follows clean backend architecture and real-world business workflows.

---

## Key Features

### Authentication & Authorization
- Custom user model with role-based access
- Login, logout, registration
- Password change and password reset
- Role-based redirects after login
- Session authentication for HTML pages
- JWT authentication for APIs

### Order Management
- Create and manage orders
- Add and manage order items
- Order status workflow (pending, confirmed, in production, delivered)
- Admin approve / reject orders

### Design Management
- Clients upload design files
- Designers view assigned designs
- Designers update design status
- Secure file uploads

### Payments
- Clients submit payments
- Admin confirms payments
- Payment summary per order

### Notifications
- System-generated notifications
- User-specific notification views
- Mark notifications as read

### Delivery & Documents
- Delivery tracking for orders
- Legal document storage per order

### Admin Dashboard
- Orders and payments summary
- System overview

## Technologies Used

- Python 3
- Django
- Django REST Framework
- Simple JWT (Authentication)
  


