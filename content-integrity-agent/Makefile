.PHONY: demo test install clean lint help

demo:
	@./run.sh demo

test:
	@./run.sh test

install:
	@./run.sh install

clean:
	@./run.sh clean

lint:
	@./run.sh lint

help:
	@./run.sh help

.PHONY: web web-dev web-install

web-install:
	cd web && npm install

web-dev:
	python3 -m api.app & cd web && npm run dev

web:
	python3 -m api.app
