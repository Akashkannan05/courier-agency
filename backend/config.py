import os

# Administrator email for receiving reports
# You can override this in your .env file
ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'admin@example.com')
