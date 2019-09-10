S3BUCKET = wgeisler-sam

.PHONY: start-local-api
start-local-api: build
	sam local start-api

packaged.yaml: .ALWAYS_REBUILD
	sam package --s3-bucket $(S3BUCKET) --output-template-file packaged.yaml

.PHONY: deploy
deploy: packaged.yaml
	sam deploy --template-file packaged.yaml --stack-name new-stack --capabilities CAPABILITY_IAM

.PHONY: build
build:
	sam build

layer.zip: requirements.txt
	docker run -t --rm -w "/opt" -v "$(PWD):/out" -v "$(PWD)/requirements.txt:/requirements.txt:ro" \
		lambci/lambda:build-python3.7 bash -c \
		"pip3 install -r /requirements.txt -t python/lib/python3.7/site-packages/ \
		&& zip -FSr /out/$@ python \
		&& chown $(shell id -u):$(shell id -g) /out/$@"

lambda-layers/project-layer.zip: $(wildcard hello_world/*.py)
	./make-project-layer.sh hello_world $@
	

.ALWAYS_REBUILD:
	

