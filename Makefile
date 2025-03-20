all: deps compile migrate loadtestdata statics media

ENV ?= prod
REGION ?= us-east-1
PYCURL_SSL_LIBRARY ?= openssl
OPENSSL_PREFIX ?= $(shell brew --prefix openssl)
LDFLAGS ?= "-L$(OPENSSL_PREFIX)/lib"
CPPFLAGS ?= "-I$(OPENSSL_PREFIX)/include"
DIR_PATH ?= .

venv:
	python3 -m venv venv

deps:
	python3 -m pip install --upgrade pip wheel setuptools
	python3 -m pip install --requirement=requirements.txt

freeze:
	python3 -m pip freeze > requirements.txt

compile:
	python3 -m compileall -qq venv || true
	python3 -m compileall $(DIR_PATH)

migrate:
	python3 manage.py migrate --noinput

migrations:
	python3 manage.py makemigrations

statics:
	python3 manage.py collectstatic --noinput

.PHONY: media
media:
	python3 manage.py collectmedia --noinput

check:
	python3 manage.py check

test:
	python3 manage.py test

testfast:
	python3 manage.py test --failfast

testsingle:
	python manage.py test $(addprefix blast.tests.,$(TEST))

run:
	python3 manage.py runserver

startlocal: ENV =
startlocal: PROCS ?= web=1,worker=1
startlocal:
	BIND=127.0.0.1 PORT=7900 foreman start -e $(ENV).env "$(PROCS)"

shell:
	python3 manage.py shell

dumptestdata:
	python3 manage.py dumpdata --natural-foreign --natural-primary \
		--exclude=admin.logentry --all --indent=2 > blast/fixtures/tests.json
	rsync -r ./media/ blast/fixtures/media/

loadtestdata: media
	python3 manage.py loaddata tests

coverage:
	coverage run python3 manage.py test
	coverage html --include=blast/*

lint:
	flake8 --max-line-length=200 $(DIR_PATH)
	black --check --exclude="venv/" --line-length=100 $(DIR_PATH) || (echo "Run 'make format' to fix formatting issues" && exit 1)
	xenon --max-absolute=C --max-modules=B --max-average=B --ignore=venv $(DIR_PATH)

format:
	isort --atomic --skip-glob="venv/*" --line-length=100 $(DIR_PATH)
	black --exclude="venv/" --line-length=100 $(DIR_PATH)

ready: format lint check test
	@echo "Ready!"

deploy:
	git push $(ENV) HEAD:master

clean:
	find blast -name __pycache__ -type d \
		-exec rm -rf {} \; 2> /dev/null || true
	rm -rf venv dist media static db.sqlite3 \
		staticfiles.json htmlcov .coverage
	mkdir media
	make venv
	sh -c "./bin/boot make"

cleandb:
	rm -f db.sqlite3
	make migrate loadtestdata

purgequeue:
	@aws --region=$(REGION) --output=json sqs purge-queue \
		--queue-url=$(shell aws --region=$(REGION) --output=json \
			sqs get-queue-url --queue-name blast-$(ENV)-$(QUEUE) --query=QueueUrl)

listqueues: QUEUE ?= ""
listqueues:
	@aws --region=$(REGION) --output=json \
		sqs list-queues --queue-name-prefix=blast-$(ENV)-$(QUEUE) | jq -r .QueueUrls[] | \
		( \
			echo "Queue\tRunning\tWaiting"; \
			while read QUEUE_URL; do \
				echo "$$QUEUE_URL" | awk -F/ '{printf $$NF"\t"}'; \
				aws --region=$(REGION) --output=json sqs get-queue-attributes --queue-url=$$QUEUE_URL --query=Attributes \
					--attribute-names ApproximateNumberOfMessagesNotVisible ApproximateNumberOfMessages | \
						jq -r '.ApproximateNumberOfMessagesNotVisible  + "\t" + .ApproximateNumberOfMessages'; \
			done \
		) | column -t

listaurorasnapshots:
	@aws --region=$(REGION) --output=json \
		rds describe-db-cluster-snapshots --db-cluster-identifier=blast-$(ENV) | \
			jq -r '.DBClusterSnapshots[] | .DBClusterIdentifier + "\t" + .SnapshotCreateTime + "\t" + .SnapshotType + "\t" + .Status + "\t" + .DBClusterSnapshotArn' | \
			sort -r -k 2 | \
			( \
				echo "Cluster\tCreated\tType\tStatus\tARN"; cat -; \
			) | column -t

createaurorasnapshot:
	aws --region=$(REGION) --output=json \
		rds create-db-cluster-snapshot --db-cluster-identifier=blast-$(ENV) \
			--db-cluster-snapshot-identifier=blast-$(ENV)-$(shell date -u +'%Y-%m-%d-%H-%M-%S')

listcdninvalidations:
	@chmod 0755 ./bin/cloudfront.sh
	@ENV=$(ENV) ./bin/cloudfront.sh listinvalidations

createcdninvalidation: PATHS ?= '/*'
createcdninvalidation:
	@chmod 0755 ./bin/cloudfront.sh
	@ENV=$(ENV) ./bin/cloudfront.sh createinvalidation $(PATHS)

flushrediscache:
	redis-cli -u "$(REDIS_URL)" flushall

monitorrediscache:
	redis-cli -u "$(REDIS_URL)" monitor

updatepublishedwidgetscount:
	python3 manage.py updatepublishedwidgetscount --client-id=$(CLIENT_ID)

updateapplicationscache:
	python3 manage.py updateapplicationscache --client-id=$(CLIENT_ID)

updateprogramscache:
	python3 manage.py updateprogramscache --client-id=$(CLIENT_ID)

updatetimelinecache:
	python3 manage.py updatetimelinecache --client-id=$(CLIENT_ID)

updatechatroomscache:
	python3 manage.py updatechatroomscache --client-id=$(CLIENT_ID)

updatestoragecaches: updatepublishedwidgetscount updateapplicationscache updateprogramscache updatetimelinecache updatechatroomscache

profilestats:
	python3 manage.py profiles --client-id=$(CLIENT_ID) stats

SINCE ?= $(shell date '+%Y-01-01T00:00:00Z')
UNTIL ?= $(shell date -u '+%Y-%m-%dT%H:%M:%SZ')

updateglobalstatistics:
	@for interval in total year month week day hour; do \
		echo heroku run:detached --remote=$(ENV) -- \
			python manage.py globalstatistics --interval=$$interval --since=$(SINCE) --until=$(UNTIL) --update --queue; \
	done

updatestatistics: updateglobalstatistics updateapplicationstatistics updateprogramstatistics updatechatroomstatistics updateaudiencestatistics 

logs: PROC ?= router
logs:
	heroku logs --remote=$(ENV) --dyno=$(PROC) --tail

logdna: APPS=access.log
logdna: TAGS=blastrt-$(ENV)
logdna:
	logdna tail --apps=$(APPS) --tags=$(TAGS) --json | jq --unbuffered --raw-output ._line

dumpenv:
	@ENV=$(ENV) ./bin/dumpenv

postdeploy:
	@chmod 0755 ./bin/postdeploy
	./bin/postdeploy

notifypreparerelease:
	@chmod 0755 ./bin/notifypreparerelease.sh
	./bin/notifypreparerelease.sh

superuser:
	python3 manage.py createsuperuser

procs:
	@awk -F: '{print $$1}' Procfile | grep -v release

depsdocs:
	npm install

prune-images:
	docker rm livelike-web livelike-cron livelike-worker
	docker rmi livelike-web livelike-cron livelike-worker

docs:
	mkdir -p dist
	$(shell npm bin)/api2html \
		-c blast/static/blast/img/logo.png \
		--out=dist/docs.html --summary \
		--languages=shell,http spec/blast-v1.yaml

cleandocs:
	rm -rf node_modules dist/docs.html
	make depsdocs

deploydocs:
	aws s3 cp --acl=public-read dist/docs.html s3://livelike-docs/api/index.html
	aws s3 cp --acl=public-read spec/blast-v1.yaml s3://livelike-docs/api/blast-v1.yaml

pushup:
	git checkout dev
	git push origin dev
	git checkout qa
	git merge dev
	git push origin qa
	git checkout staging
	git merge qa
	git push origin staging
	git checkout master
	git merge staging
	git push origin master
	git checkout dev

pushdown:
	git checkout master
	git push origin master
	git checkout staging
	git merge master
	git push origin staging
	git checkout qa
	git merge staging
	git push origin qa
	git checkout dev
	git merge qa
	git push origin dev
	git checkout master

ansible:
	ansible-playbook  ./blastrt/nginx-docker.yml --extra-vars "env=local grid=blastrt region=us-east-1" --inventory localhost

containers:
	make ansible
	docker-compose up

notifyrelease:
	python ./bin/notify.py $(BRANCH)

