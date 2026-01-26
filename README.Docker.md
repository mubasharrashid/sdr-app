# Docker Deployment Guide

This guide explains how to build and deploy the SDR App using Docker.

## Prerequisites

- Docker 20.10+ installed
- Docker Compose 2.0+ installed (optional, for docker-compose)
- Environment variables configured (see `.env.example`)

## Quick Start

### 1. Production Build

```bash
# Build the Docker image
docker build -t sdr-app:latest .

# Run the container
docker run -d \
  --name sdr-app \
  -p 8000:8000 \
  --env-file .env \
  sdr-app:latest
```

### 2. Using Docker Compose (Production)

```bash
# Make sure your .env file is configured
cp .env.example .env
# Edit .env with your actual values

# Start the application
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the application
docker-compose down
```

### 3. Development Mode

```bash
# Using docker-compose for development
docker-compose -f docker-compose.dev.yml up

# Or build and run development Dockerfile
docker build -f Dockerfile.dev -t sdr-app:dev .
docker run -d \
  --name sdr-app-dev \
  -p 8000:8000 \
  --env-file .env \
  -v $(pwd):/app \
  sdr-app:dev
```

## Environment Variables

The following environment variables are required:

### Required Variables

- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_SERVICE_ROLE_KEY` - Supabase service role key
- `DATABASE_URL` - PostgreSQL database connection string

### Optional Variables

- `APP_ENV` - Environment (development/production), default: `development`
- `APP_DEBUG` - Enable debug mode, default: `true`
- `SECRET_KEY` - Secret key for JWT/sessions, default: `dev-secret-key-change-in-production`
- `SUPABASE_ANON_KEY` - Supabase anonymous key (optional)
- `DB_POOL_SIZE` - Database pool size, default: `5`
- `DB_MAX_OVERFLOW` - Database max overflow, default: `10`
- `DB_POOL_TIMEOUT` - Database pool timeout, default: `30`

## Docker Commands

### Build

```bash
# Production build
docker build -t sdr-app:latest .

# Development build
docker build -f Dockerfile.dev -t sdr-app:dev .
```

### Run

```bash
# Run container
docker run -d \
  --name sdr-app \
  -p 8000:8000 \
  --env-file .env \
  sdr-app:latest

# Run with custom environment variables
docker run -d \
  --name sdr-app \
  -p 8000:8000 \
  -e SUPABASE_URL=your-url \
  -e SUPABASE_SERVICE_ROLE_KEY=your-key \
  -e DATABASE_URL=your-db-url \
  sdr-app:latest
```

### Management

```bash
# View logs
docker logs -f sdr-app

# Stop container
docker stop sdr-app

# Start container
docker start sdr-app

# Remove container
docker rm sdr-app

# Execute command in container
docker exec -it sdr-app bash

# View container stats
docker stats sdr-app
```

## Health Check

The container includes a health check endpoint at `/health`. You can verify the application is running:

```bash
# Check health
curl http://localhost:8000/health

# Or from inside the container
docker exec sdr-app curl http://localhost:8000/health
```

## Production Deployment

### Best Practices

1. **Use Environment Variables**: Never hardcode secrets in Dockerfiles
2. **Use Secrets Management**: For production, use Docker secrets or external secret managers
3. **Resource Limits**: Set appropriate CPU and memory limits
4. **Logging**: Configure proper logging and log rotation
5. **Monitoring**: Set up monitoring and alerting
6. **Backup**: Regular database backups

### Example with Resource Limits

```bash
docker run -d \
  --name sdr-app \
  -p 8000:8000 \
  --env-file .env \
  --memory="512m" \
  --cpus="1.0" \
  --restart=unless-stopped \
  sdr-app:latest
```

### Using Docker Compose with Resource Limits

```yaml
services:
  api:
    # ... existing configuration ...
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M
```

## Troubleshooting

### Container won't start

1. Check environment variables are set correctly
2. Verify database connection string
3. Check logs: `docker logs sdr-app`

### Database connection errors

1. Ensure `DATABASE_URL` is correct
2. Check network connectivity from container
3. Verify database is accessible

### Port already in use

```bash
# Change port mapping
docker run -d \
  --name sdr-app \
  -p 8001:8000 \  # Use different host port
  --env-file .env \
  sdr-app:latest
```

## Multi-Stage Build Benefits

The production Dockerfile uses multi-stage builds to:

- Reduce final image size
- Improve security (minimal runtime dependencies)
- Faster builds (better layer caching)
- Separate build and runtime environments

## Security Notes

- The production image runs as a non-root user (`appuser`)
- Only necessary packages are installed
- Secrets should be passed via environment variables or secrets management
- Regularly update base images and dependencies

## Support

For issues or questions, please check the main README or contact the development team.
