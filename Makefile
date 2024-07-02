all: clean docker

clean:
	rm -rf build/ dist/ docker/*.whl

py_wheel:
	python3 -m build --wheel

docker: py_wheel
	TAG=$(git tag)
	find dist  -iname '*.whl' -exec mv {} docker/ \;
	docker-compose --project-directory docker build