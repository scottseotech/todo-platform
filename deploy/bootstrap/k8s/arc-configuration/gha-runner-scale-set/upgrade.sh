#!/bin/bash -xe

# Check if an argument is provided
if [ -z "$1" ]; then
  echo "Usage: $0 <image-tag>"
  echo "Example: $0 v1.2.3"
  exit 1
fi

# Update the image in values.yaml using yq
yq eval -i '.template.spec.containers[0].image = "curiosinauts/scottseotech-runner:'${1}'"' custom-values.yaml

# running the following helm upgrade in GHA runner fails 
# because GHA runner uses different account than my local k8s user account
# better to execute helm-upgrade.sh which has the following 

git add .

git commit -m "updating ARC runner version to ${1}"

git push