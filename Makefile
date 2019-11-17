PYTHON=python3


.PHONY: test
test:
	$(PYTHON) -m unittest discover -v

.PHONY: wheel
wheel:
	$(PYTHON) setup.py bdist_wheel

.PHONY: packaged
packaged: onconnect.zip ondisconnect.zip taskexecute.zip taskresult.zip

%.zip: sam-app/%
	mkdir -p packaged
	cd $< && zip -FSr $(PWD)/packaged/$@ ./