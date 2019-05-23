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

@test "test container ran with success" {
	sleep 10
	run docker logs $CONTAINER
	assert_output --partial 'SUCCESSES: 1'
}

@test "clean test containers" {
	run docker-compose down
	assert_success
}
