#!/usr/bin/env bash

# Check if a certain image Dockerfile has changed, in our case OS .
# The current command should be run in the docker directory.
# If we detect changes against origin/dev we build and push new image.

check_image () {
  old=$(date +%s --date '30 days ago')
  dhub=$(date +%s --date=$(curl -X GET https://registry.hub.docker.com/v2/repositories/nbisweden/ega-$1/tags/latest/ | jq -r '.last_updated'))
  if [ $old \> $dhub ]
  then
    printf 'ega-%s base image is to old, building new ega-%s image.\n' "$1" "$1"
    make -C images "$1"
    printf 'pushing new ega-%s image.\n' "$1"
    docker push "nbisweden/ega-$1"
  else
    printf 'New ega-%s docker image is not required.\n' "$1"
  fi
}

check_image "$1"
