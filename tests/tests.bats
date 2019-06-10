#!/usr/bin/env bats

load 'test_helper/bats-support/load'
load 'test_helper/bats-assert/load'
load test_helpers

IMAGE="bats-opbeans"
CONTAINER="opbeans-loadgen"

@test "build image" {
	cd $BATS_TEST_DIRNAME/..
	run docker-compose build
	assert_success
}

@test "create test container" {
	run docker-compose up -d
	assert_success
}

@test "test container is running" {
	run docker inspect -f {{.State.Running}} $CONTAINER
	assert_output --partial 'true'
}

@test "test container ran OK" {
	# Docker container might take a bit to be up and running. Let's wait a bit
	sleep 30
	run docker logs $CONTAINER
	assert_output --partial 'OK'
}

@test "clean test containers" {
	run docker-compose down
	assert_success
}
