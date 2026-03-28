
### ENV SETUP ------------------------------ ###

setup: requirements.txt
	python -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -r requirements.txt

clean: .venv
	rm -r .venv

### AGENT RUN ------------------------------ ###

agent_run: setup
	.venv/bin/python3 -m streamlit run src/__main__.py

### UNIT TESTS ----------------------------- ###

interface_unit_test: setup
	.venv/bin/python3 -m streamlit run unit_tests/interface_test.py

memory_unit_test: setup
	.venv/bin/python3 -m unit_tests.memory_test

orchestrator_unit_test: setup
	.venv/bin/python3 -m unit_tests.orchestrator_test
