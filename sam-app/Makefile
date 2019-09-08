
.PHONY: start-local-api
start-local-api: build
	sam local start-api


.PHONY: build
build:
	sam build

layer.zip: requirements.txt
	docker run -t --rm -w "/opt" -v "$(PWD):/out" -v "$(PWD)/requirements.txt:/requirements.txt:ro" \
		lambci/lambda:build-python3.7 bash -c \
		"pip3 install -r /requirements.txt -t python/lib/python3.7/site-packages/ "\
		"&& zip -FSr /out/$@ python "\
		"&& chown $(shell id -u):$(shell id -g) /out/$@"
