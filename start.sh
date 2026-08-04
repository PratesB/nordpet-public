#!/bin/bash

# Press Ctrl+C (kills all child processes)
trap "kill 0" EXIT

echo "Starting Tailwind CSS in the background..."
npm run tailwind:watch &

echo "Starting Django server..."
venv/bin/python manage.py runserver &

# Wait close the terminal or press Ctrl+C
wait
