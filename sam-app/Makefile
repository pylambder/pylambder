S3BUCKET = ajopek-test-bucket
CLOUDFORMATION_STACK = websocket-task-poc

packaged.yaml: .ALWAYS_REBUILD lambda-layers/dependencies-layer.zip lambda-layers/project-layer.zip
	sam package --s3-bucket $(S3BUCKET) --output-template-file packaged.yaml

.PHONY: start-local-api
start-local-api: build
	sam local start-api

.PHONY: deploy
deploy: packaged.yaml
	sam deploy --template-file packaged.yaml --stack-name $(CLOUDFORMATION_STACK) --capabilities CAPABILITY_IAM

.PHONY: build
build:
	sam build

lambda-layers/dependencies-layer.zip: requirements.txt
	docker run -t --rm -w "/opt" -v "$(PWD):/out" -v "$(PWD)/requirements.txt:/requirements.txt:ro" \
		lambci/lambda:build-python3.7 bash -c \
		"pip3 install -r /requirements.txt -t python/lib/python3.7/site-packages/ \
		&& zip -FSr /out/$@ python \
		&& chown $(shell id -u):$(shell id -g) /out/$@"

lambda-layers/project-layer.zip: $(wildcard ../sample/*.py) $(wildcard ../pylambder/*.py)
	cp -a ../pylambder ../sample/
	./make-project-layer.sh ../sample $@
	rm -rf ../sample/pylambder
	

.ALWAYS_REBUILD:
	

