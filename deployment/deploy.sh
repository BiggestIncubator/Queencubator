#!/bin/bash
set -eu

cd "$(dirname "$0")"

echo "pull new image."
docker-compose pull

echo "up all containers."
docker-compose up -d

echo "restart nginx" 
docker exec nginx nginx -t && docker exec nginx nginx -s reload
