# Deployment Guide for Label Manager

## Required Environment Variables

When deploying this application, the following environment variables must be set:

### Database Connection Variables
You must set either `DATABASE_URL` or the individual PostgreSQL connection variables:

- `DATABASE_URL`: Complete PostgreSQL connection string in the format:
  `postgresql://username:password@host:port/database`

OR the individual components:

- `PGUSER`: PostgreSQL username
- `PGPASSWORD`: PostgreSQL password
- `PGDATABASE`: PostgreSQL database name
- `PGHOST`: PostgreSQL host (defaults to "localhost" if not set)
- `PGPORT`: PostgreSQL port (defaults to "5432" if not set)

### Security Variables
- `FLASK_SECRET_KEY`: Secret key for Flask session encryption and CSRF protection

### API Credentials (Optional)
For full functionality, you may need:
- `CRAFTMYPDF_API_KEY`: Your CraftMyPDF API key (can also be set in application settings)
- `SQUARE_ACCESS_TOKEN`: Your Square API access token (can also be set in application settings)
- `SQUARE_LOCATION_ID`: Your Square location ID (can also be set in application settings)

## Deployment Steps

1. Ensure all required environment variables are set in your Replit deployment settings
2. Run the following database migrations if needed:
   ```
   FLASK_APP=app.py flask db upgrade
   ```
3. Click the Deploy button in Replit

## Verifying the Deployment

After deploying:
1. Check the logs to ensure the app started correctly
2. Verify database connection is successful
3. Test user login and product management features

## Troubleshooting

If deployment fails with a message about missing environment variables:
1. Check that all required variables listed above are set
2. Verify the database credentials are correct
3. Ensure the PostgreSQL database is accessible from the deployment environment