#!/bin/bash

# Install svu from https://github.com/caarlos0/svu
# Install gum from https://github.com/charmbracelet/gum

# chore: foo	Nothing
# fix: fixed something	Patch
# feat: added new button to do X	Minor
# fix: fixed thing xyz
# BREAKING CHANGE: this will break users because of blah	Major
# fix!: fixed something	Major
# feat!: added blah	Major

part=$(gum choose next patch minor major)

version=$(svu ${part})

echo "Creating git tag ${version}..."
git tag "${version}"

echo "Pushing changes and tags..."
git push origin HEAD
git push origin "${version}"