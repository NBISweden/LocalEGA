#!/bin/bash

for submodule in $( git submodule status | awk '{print $2}' ); do
    cd $submodule
    ## Skip if we already have this remote
    if [[ $( git remote | grep elixir ) ]]; then
        continue
    fi
    ## Add elixir remote
    echo "Adding elixir remote for $submodule"
    git remote add elixir https://github.com/elixir-europe/${submodule}.git
    git fetch elixir
    cd ..
done
