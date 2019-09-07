PYTHON=python3

.PHONY: wheel
wheel:
	$(PYTHON) setup.py bdist_wheel
