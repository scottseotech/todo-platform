#!/bin/bash
# Install Snapshot CRDs required by Democratic CSI
# The Democratic CSI Helm chart requires these CRDs to be pre-installed

set -e

echo "Installing Snapshot CRDs for Democratic CSI..."

# Install snapshot CRDs from kubernetes-csi/external-snapshotter v8.0.1
kubectl apply -f https://raw.githubusercontent.com/kubernetes-csi/external-snapshotter/v8.0.1/client/config/crd/snapshot.storage.k8s.io_volumesnapshotclasses.yaml
kubectl apply -f https://raw.githubusercontent.com/kubernetes-csi/external-snapshotter/v8.0.1/client/config/crd/snapshot.storage.k8s.io_volumesnapshotcontents.yaml
kubectl apply -f https://raw.githubusercontent.com/kubernetes-csi/external-snapshotter/v8.0.1/client/config/crd/snapshot.storage.k8s.io_volumesnapshots.yaml

echo "✓ Snapshot CRDs installed successfully"
