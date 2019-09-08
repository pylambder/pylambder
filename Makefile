PYTHON=python3


.PHONY: test
test:
	$(PYTHON) -m unittest discover

.PHONY: wheel
wheel:
	$(PYTHON) setup.py bdist_wheel
