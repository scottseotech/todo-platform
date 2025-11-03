#!/bin/bash

# Install svu from https://github.com/caarlos0/svu
# Install gum from https://github.com/charmbracelet/gum

part=$(gum choose next patch minor major)

version=$(svu ${part})

echo "Creating git tag ${version}..."
git tag "${version}"

echo "Pushing changes and tags..."
git push origin HEAD
git push origin "${version}"