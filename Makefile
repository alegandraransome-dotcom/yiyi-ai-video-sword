.PHONY: validate test build clean

validate:
	PYTHONPATH=src python -m yi_runtime validate .

test:
	PYTHONPATH=src python -m unittest discover -s tests -v

build: validate test
	PYTHONPATH=src python -m yi_runtime build .

clean:
	rm -rf build dist src/*.egg-info src/yi_director_runtime.egg-info
