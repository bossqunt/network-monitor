# Build and run with Docker Compose
docker-compose up -d

# Build only
docker-compose build

# View logs
docker-compose logs -f network_monitor

# View Grafana logs
docker-compose logs -f grafana

# Stop
docker-compose down

# Stop and remove volumes (deletes all data)
docker-compose down -v

# Restart just the monitor
docker-compose restart network_monitor

# Restart Grafana
docker-compose restart grafana

# Execute command in container
docker-compose exec network_monitor python -c "print('Hello')"

# Access MySQL
docker-compose exec mysql mysql -u root -punknown network_monitor

# Access Grafana
# Open http://localhost:3000 in browser
# Default login: admin/admin
