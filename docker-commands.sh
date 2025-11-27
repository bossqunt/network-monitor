# Build and run with Docker Compose
docker-compose up -d

# Build only
docker-compose build

# View logs
docker-compose logs -f network_monitor

# Stop
docker-compose down

# Stop and remove volumes (deletes all data)
docker-compose down -v

# Restart just the monitor
docker-compose restart network_monitor

# Execute command in container
docker-compose exec network_monitor python -c "print('Hello')"

# Access MySQL
docker-compose exec mysql mysql -u root -punknown network_monitor
