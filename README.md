# PrintFlow Project

PrintFlow is designed to manage print orders from creation to delivery.  
The system supports three user roles:

- **Client** – places orders, uploads designs, makes payments  
- **Designer** – handles design requests and updates design status  
- **Admin** – manages users, orders, payments, approvals, and system reports  

---

## Key Features

### Authentication & Authorization
- Custom user model with role-based access  
- Login, logout, registration  
- Password change and password reset  
- Role-based redirects after login  
- JWT authentication for APIs  

### Order Management
- Create and manage orders  
- Add and manage order items  
- Order status workflow: **pending → confirmed → in production → delivered**  
  

### Design Management
- Clients can upload design files  
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

---

## Frontend Features
- Built with **React (JSX)** and **Vite**  
- API integration using **Axios**  
- State management using **Redux Toolkit**  
- Role-based UI rendering  
- Protected routes for authenticated users  
- Dynamic dashboards for different user roles  
- Form handling and validation  

---

## Technologies Used

### Backend
- Python 3  
- Django  
- Django REST Framework (DRF)  
- Simple JWT (Authentication)  

### Frontend
- React (JSX)  
- Vite  
- Axios  
- Redux Toolkit  


  


