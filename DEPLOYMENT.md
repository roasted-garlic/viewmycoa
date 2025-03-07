# Deployment Guide for Label Manager

## Environment Variables

### Database Connection Variables (Recommended but Optional)
For production use, we recommend setting up a PostgreSQL database using either:

- `DATABASE_URL`: Complete PostgreSQL connection string in the format:
  `postgresql://username:password@host:port/database`

OR the individual components:

- `PGUSER`: PostgreSQL username
- `PGPASSWORD`: PostgreSQL password
- `PGDATABASE`: PostgreSQL database name
- `PGHOST`: PostgreSQL host (defaults to "localhost" if not set)
- `PGPORT`: PostgreSQL port (defaults to "5432" if not set)

**NOTE: The application will automatically fall back to a SQLite database if no PostgreSQL variables are set.** This is suitable for testing or low-traffic deployments but not recommended for production use with multiple concurrent users.

### Security Variables (Recommended but Optional)
- `FLASK_SECRET_KEY`: Secret key for Flask session encryption and CSRF protection
  - If not set, a default development key will be used (not recommended for production)

### API Credentials (Optional)
For full functionality, you may need:
- `CRAFTMYPDF_API_KEY`: Your CraftMyPDF API key (can also be set in application settings)
- `SQUARE_ACCESS_TOKEN`: Your Square API access token (can also be set in application settings)
- `SQUARE_LOCATION_ID`: Your Square location ID (can also be set in application settings)

## Deployment Steps

1. Set the following REQUIRED environment variables in your Replit deployment settings:
   - `FLASK_SECRET_KEY`: A secure random string for session encryption
   - Either set `DATABASE_URL` or all of these PostgreSQL variables: `PGDATABASE`, `PGHOST`, `PGPORT`, `PGUSER`, `PGPASSWORD`
2. Click the Deploy button in Replit
3. Check logs to ensure all variables are properly configured

## Verifying the Deployment

After deploying:
1. Check the logs to ensure the app started correctly
2. Verify you can log in with the default admin account if you haven't created any users yet:
   - Username: `admin`
   - Password: `admin` (be sure to change this after first login)
3. Test user login and product management features

## Troubleshooting

If you see warnings about using SQLite in deployment:
- This is expected behavior if PostgreSQL variables are not configured
- The application will still work, but for production use with multiple users, PostgreSQL is recommended

If you need to migrate to PostgreSQL later:
1. Set up the required PostgreSQL environment variables
2. Export your data from SQLite and import it to PostgreSQL (contact support for assistance)