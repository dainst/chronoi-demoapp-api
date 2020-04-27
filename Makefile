
run:
	FLASK_ENV=development poetry run ./app.py

test:
	FLASK_ENV=testing poetry run ./apitest.py
