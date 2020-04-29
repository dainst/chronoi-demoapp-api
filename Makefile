

run:
	FLASK_ENV=development poetry run ./app.py

test:
	FLASK_ENV=testing poetry run ./integration_test.py

docker-build:
	docker build --tag dainst/demoapp:dev $(CURDIR)

docker-run:
	- docker rm -f demoapp
	docker run --name demoapp \
			-it \
			-v $(CURDIR):/app \
			-e FLASK_ENV=development \
			-p 8080:8080 \
			dainst/demoapp:dev

docker-test:
	- docker rm -f demoapp-test
	docker run --name demoapp-test \
			-v $(CURDIR):/app \
			-e FLASK_ENV=testing \
			--entrypoint "/app/integration_test.py" \
			dainst/demoapp:dev

docker-clean:
	- docker rm -f demoapp demoapp-test
	docker rmi dainst/demoapp:dev
