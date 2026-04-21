
### ENV SETUP ------------------------------ ###

setup: requirements.txt
	python -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -r requirements.txt

clean: .venv
	rm -r .venv

### AGENT RUN ------------------------------ ###

summarize: setup
	.venv/bin/python3 -m streamlit run src/__main__.py
