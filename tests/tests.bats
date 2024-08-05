#!/usr/bin/env bats

load 'test_helper/bats-support/load'
load 'test_helper/bats-assert/load'
load test_helpers

IMAGE="bats-opbeans"
CONTAINER="opbeans-loadgen"

@test "Build image" {
	cd $BATS_TEST_DIRNAME/..
	run docker compose build
	assert_success
}

# Test Procfile-based run
@test "Create test container [Procfile mode]" {
	run docker compose up -d
	assert_success
}

@test "Test container is running [Procfile mode]" {
	run docker inspect -f {{.State.Running}} $CONTAINER
	assert_output --partial 'true'
}

@test "Test container ran OK [Procfile mode]" {
	# Docker container might take a bit to be up and running. Let's wait a bit
	sleep 30
	run docker logs $CONTAINER
	assert_output --partial 'OK'
}

@test "Clean test containers [Procfile mode]" {
	run docker compose down
	assert_success
}

# Test Dyno-based run
@test "Create test container [Dyno mode]" {
	run docker compose --env-file $BATS_TEST_DIRNAME/dyno.env up -d
	assert_success
}

@test "Test container is running [Dyno mode]" {
	run docker inspect -f {{.State.Running}} $CONTAINER
	assert_output --partial 'true'
}

@test "Test container ran OK [Dyno mode]" {
	# Docker container might take a bit to be up and running. Let's wait a bit
	sleep 30
	run docker logs $CONTAINER
	assert_output --partial 'OK'
}

@test "Clean test containers [Dyno mode]" {
	run docker compose down
	assert_success
}
