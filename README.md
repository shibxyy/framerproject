# Framer Project

An agricultural marketplace web application built with Django that directly connects farmers and consumers.

## Features

- **Farmer Portal**:
  - Registration and profile verification
  - Manage product listings, pricing, and stock inventory
  - Order management and sales tracking
  - Customer review and performance reports

- **Consumer Portal**:
  - Browse marketplace categories and search farm products
  - Shopping cart and checkout system
  - Order tracking and order history
  - Product feedback and reviews

- **Admin Dashboard**:
  - Verification and approval workflow for farmers and products
  - Category management
  - Order monitoring and complaints resolution
  - Overall marketplace analytics and reports

## Tech Stack

- **Backend**: Python 3, Django
- **Database**: SQLite (default / development)
- **Frontend**: HTML5, CSS3, JavaScript, Django Templates
- **Media / Image Handling**: Pillow

## Getting Started

### Prerequisites

- Python 3.10 or higher
- `pip` package manager

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/shibxyy/framerproject.git
   cd framerproject
   ```

2. **Create and activate a virtual environment:**
   ```bash
   # Windows (PowerShell)
   python -m venv venv
   .\venv\Scripts\Activate.ps1

   # macOS / Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Apply database migrations:**
   ```bash
   python manage.py migrate
   ```

5. **Create a superuser (optional, for admin access):**
   ```bash
   python manage.py createsuperuser
   ```

6. **Start the development server:**
   ```bash
   python manage.py runserver
   ```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your web browser.
