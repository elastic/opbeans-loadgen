# Opbeans Load Generator

This is a load generator for [Opbeans](https://github.com/elastic?utf8=%E2%9C%93&q=Opbeans&type=&language=) as a Docker container.

Start the docker container with a list of base URLs to generate load on

    docker run --rm -e OPBEANS_URLS=opbeans-node:http://opbeans-node:3000,opbeans-python:http://opbeans-python:3000 opbeans/opbeans-loadgen

## Testing locally

The simplest way to test this demo is by running:

```bash
make test
```

Tests are written using [bats](https://github.com/sstephenson/bats) under the tests dir

## Publishing to dockerhub locally

Publish the docker image with

```bash
VERSION=1.2.3 make publish
```

NOTE: VERSION refers to the tag for the docker image which will be published in the registry
