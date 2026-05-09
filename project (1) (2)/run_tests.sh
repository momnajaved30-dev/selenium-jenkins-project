#!/bin/bash
# Start the Flask application in the background
export FLASK_APP=application.py
export FLASK_ENV=development

# Run flask server
python application.py &
FLASK_PID=$!

# Wait for the server to be ready
echo "Waiting for Flask server to start..."
sleep 5

# Run the Selenium tests
echo "Running tests..."
python -m unittest test_ecommerce.py
TEST_EXIT_CODE=$?

# Kill the Flask server
echo "Stopping Flask server..."
kill $FLASK_PID

# Exit with the test suite's exit code
exit $TEST_EXIT_CODE
