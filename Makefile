PYTHON=python3


.PHONY: test
test:
	$(PYTHON) -m unittest discover -v

.PHONY: wheel
wheel: packaged
	$(PYTHON) setup.py bdist_wheel

.PHONY: sdist
sdist: packaged
	$(PYTHON) setup.py sdist

.PHONY: packaged
packaged: onconnect.zip ondisconnect.zip taskexecute.zip taskresult.zip authorizer.zip

%.zip: sam-app/%
	mkdir -p packaged
	cd $< && zip -FSr $(PWD)/packaged/$@ ./
