### ENV SETUP ------------------------------ ###

setup: requirements.txt
	python -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -r requirements.txt

clean: .venv
	rm -r .venv

### AGEN RUN ------------------------------- ###

agent: setup
	.venv/bin/python3 -m src

### UNIT TESTS ----------------------------- ###

memory_unit_test: setup
	.venv/bin/python3 -m unit_tests.memory_test

skills_simple_unit_test: setup
	.venv/bin/python3 -m -m unit_tests.skills_test_simple

skills_full_unit_test: setup
	.venv/bin/python3 -m -m unit_tests.skills_test_complex