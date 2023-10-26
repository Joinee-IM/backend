#!/bin/bash

DEPLOY_ENV=$1
IMAGE_TAG=$2

helm upgrade cloud-native-backend deploy/helm/charts \
    --install \
    --namespace=cloud-native-"${DEPLOY_ENV}"  \
    --values deploy/helm/"${DEPLOY_ENV}"/values.yaml \
    --set image.tag="${IMAGE_TAG}"
