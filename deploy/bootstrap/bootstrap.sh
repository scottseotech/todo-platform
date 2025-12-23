#!/bin/bash -e

# K3s node configuration
setup_node() {
    K3S_NODE_IP=$(gum input --placeholder="Enter k8s node ip" --value="192.168.30.10")
    K3S_CONTEXT=$(gum input --placeholder="Enter k8s context" --value="k3s")
    K3S_USER=$(gum input --placeholder="Enter k8s node user" --value="root")

    gum style --foreground 99 --border-foreground 99 --border double --align center --width 50 --margin "1 2" --padding "2 4" "Setting Up K3s Node Configuration"

    echo "Configuring Docker Hub registry settings..."
    scp registries.yaml root@$K3S_NODE_IP:/etc/rancher/k3s/registries.yaml

    echo "Restarting K3s service to apply changes..."
    ssh root@$K3S_NODE_IP systemctl force-reload k3s
    
    echo "Waiting for K3s to be ready..."
    sleep 5

    scp $K3S_USER@$K3S_NODE_IP:/etc/rancher/k3s/k3s.yaml ~/.kube/$K3S_NODE_IP.k3s

    echo "Renaming default to $K3S_CONTEXT"
    sed -i.bak "s/default/$K3S_CONTEXT/g" ~/.kube/$K3S_NODE_IP.k3s

    echo "Updating kubeconfig server IP..."
    sed -i.bak "s/127.0.0.1/$K3S_NODE_IP/g" ~/.kube/$K3S_NODE_IP.k3s

    export KUBECONFIG=~/.kube/config:~/.kube/$K3S_NODE_IP.k3s
    kubectl config view --merge --flatten > ~/.kube/merged-config
    mv ~/.kube/merged-config ~/.kube/config
    chmod 600 ~/.kube/config
    
    echo "Testing kubectl connection..."
    if kubectl get nodes &>/dev/null; then
        gum style --foreground 46 --bold "✓ K3s node configuration and kubectl access completed!"
        rm ~/.kube/$K3S_NODE_IP.k3s
        rm ~/.kube/$K3S_NODE_IP.k3s.bak
    else
        gum style --foreground 196 --bold "❌ kubectl connection test failed"
    fi

    gum style --foreground 240 "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

deploy_democratic_csi() {
    K3S_CONTEXT=$(gum input --placeholder="Enter k8s context" --value="k3s")
    kubectl ctx $K3S_CONTEXT
    kubectl create namespace democratic-csi || true

    # democratic-csi requires snapshot CRDs
    kubectl apply -f https://raw.githubusercontent.com/kubernetes-csi/external-snapshotter/v8.0.1/client/config/crd/snapshot.storage.k8s.io_volumesnapshotclasses.yaml
    kubectl apply -f https://raw.githubusercontent.com/kubernetes-csi/external-snapshotter/v8.0.1/client/config/crd/snapshot.storage.k8s.io_volumesnapshotcontents.yaml
    kubectl apply -f https://raw.githubusercontent.com/kubernetes-csi/external-snapshotter/v8.0.1/client/config/crd/snapshot.storage.k8s.io_volumesnapshots.yaml

    gum style --foreground 46 --border-foreground 46 --border double --align center --width 50 --margin "1 2" --padding "2 4" "Deploying Democratic CSI Resources"

    echo "Applying Democratic CSI manifests..."
    kubectl apply -f k8s/csi/all-resources-democratic-csi.yaml
    kubectl apply -f k8s/csi/storageclass.yaml
    kubectl apply -f k8s/csi/pvc.yaml

    echo "Waiting for Democratic CSI deployment to be ready..."
    kubectl wait --for=condition=ready pod -l app=democratic-csi -n democratic-csi --timeout=300s || true
    
    gum style --foreground 46 --bold "✓ Democratic CSI deployment completed!"

    gum style --foreground 240 "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

deploy_metallb() {
    K3S_CONTEXT=$(gum input --placeholder="Enter k8s context" --value="k3s")
    kubectl ctx $K3S_CONTEXT

    IP_RANGE=$(gum input --placeholder="Enter IP range (e.g., 192.168.30.80-192.168.30.90)" --value="192.168.30.xx-192.168.30.yy")

    gum style --foreground 212 --border-foreground 212 --border double --align center --width 50 --margin "1 2" --padding "2 4" "Deploying MetalLB K8s Resources"

    helm repo add metallb https://metallb.github.io/metallb || true

    # Create MetalLB namespace with special previleges
    kubectl apply -f k8s/metallb/metallb-namespace.yaml

    kubectl apply -f https://raw.githubusercontent.com/metallb/metallb/v0.14.9/config/manifests/metallb-native.yaml

    echo "Waiting for MetalLB deployment to be ready..."
    kubectl wait --for=condition=ready pod -l app=metallb -n metallb-system --timeout=300s
    kubectl wait --for=condition=ready pod -l component=speaker -n metallb-system --timeout=300s

    sed -i.bak "s/replaceme/$IP_RANGE/g" k8s/metallb/ip-range.yaml
    kubectl apply -f k8s/metallb/ip-range.yaml
    rm k8s/metallb/ip-range.yaml.bak
    git checkout k8s/metallb/ip-range.yaml

    gum style --foreground 240 "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

deploy_argocd() {
    gum style --foreground 75 --border-foreground 75 --border double --align center --width 50 --margin "1 2" --padding "2 4" "Deploying ArgoCD K8s Resources"

    kubectl create namespace argocd || true

    # firewall might be blocking outgoing port 22. this makes connecting to github.com on port 22 timeout sometimes.
    # therefore, we apply ssh_config to argocd
    kubectl create secret generic argocd-ssh-config --from-file=config=./k8s/argocd/ssh_config -n argocd || true

    # download the original and make sure existing changes are copied over
    # https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
    # kubectl -n argocd apply -f ./k8s/argocd/argocd-install.yaml || true
    kustomize build ./k8s/argocd --enable-helm | kubectl apply -n argocd -f -

    kubectl -n argocd apply -f ./k8s/argocd/argocd-ingress.yml || true

    kubectl patch svc argocd-server -n argocd -p '{"spec": {"type": "LoadBalancer"}}'

    echo "Waiting for ArgoCD deployment to be ready..."
    kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=argocd-server -n argocd --timeout=300s
    kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=argocd-application-controller -n argocd --timeout=300s
    kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=argocd-repo-server -n argocd --timeout=300s
    
    echo "ArgoCD deployment completed successfully!"

    # Get initial admin password and server IP
    ADMIN_PASSWORD=$(kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d)
    SERVER_IP=$(kubectl get svc -n argocd | grep argocd-server | grep -v metrics | awk '{ print $4 }')
    
    gum style --foreground 226 --bold "ArgoCD Server Details:"
    echo "Server IP: $SERVER_IP"
    echo "Initial Admin Password: $ADMIN_PASSWORD"
    
    # Login to ArgoCD
    argocd login $SERVER_IP --username admin --password $ADMIN_PASSWORD --insecure
    
    # Get new password from user with confirmation
    while true; do
        NEW_PASSWORD=$(gum input --password --placeholder "Enter new admin password")
        CONFIRM_PASSWORD=$(gum input --password --placeholder "Confirm new admin password")
        
        if [ "$NEW_PASSWORD" = "$CONFIRM_PASSWORD" ]; then
            break
        else
            gum style --foreground 196 --bold "❌ Passwords do not match. Please try again."
        fi
    done
    
    # Update admin password
    argocd account update-password --current-password $ADMIN_PASSWORD --new-password $NEW_PASSWORD
    
    gum style --foreground 46 --bold "✓ Admin password updated successfully!"
    
    # Add repository
    argocd repo add git@github.com:scottseotech/todo-platform.git --ssh-private-key-path ~/.ssh/id_ed25519
    
    # Apply app-of-apps
    kubectl apply -f k8s/argocd/app-of-apps.yaml -n argocd || true

    gum style --foreground 46 --bold "✓ ArgoCD setup completed! You can now monitor with:"
    echo "kubectl logs -n argocd statefulset/argocd-application-controller -f"

    gum style --foreground 240 "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

deploy_prometheus_operator() {
    gum style --foreground 220 --border-foreground 220 --border double --align center --width 50 --margin "1 2" --padding "2 4" "Deploying Prometheus Operator CRDs"

    echo "Installing Prometheus Operator CRDs (including ServiceMonitor)..."
    kubectl apply --server-side -f https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/main/example/prometheus-operator-crd/monitoring.coreos.com_alertmanagerconfigs.yaml
    kubectl apply --server-side -f https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/main/example/prometheus-operator-crd/monitoring.coreos.com_alertmanagers.yaml
    kubectl apply --server-side -f https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/main/example/prometheus-operator-crd/monitoring.coreos.com_prometheuses.yaml
    kubectl apply --server-side -f https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/main/example/prometheus-operator-crd/monitoring.coreos.com_servicemonitors.yaml
    kubectl apply --server-side -f https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/main/example/prometheus-operator-crd/monitoring.coreos.com_prometheusrules.yaml
    kubectl apply --server-side -f https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/main/example/prometheus-operator-crd/monitoring.coreos.com_podmonitors.yaml
    kubectl apply --server-side -f https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/main/example/prometheus-operator-crd/monitoring.coreos.com_probes.yaml
    echo "Verifying ServiceMonitor CRD installation..."
    kubectl get crd servicemonitors.monitoring.coreos.com && gum style --foreground 46 --bold "✓ ServiceMonitor CRD successfully installed!" || gum style --foreground 196 --bold "❌ ServiceMonitor CRD installation failed"

    gum style --foreground 240 "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

deploy_cnpg_operator() {
    gum style --foreground 33 --border-foreground 33 --border double --align center --width 50 --margin "1 2" --padding "2 4" "Deploying CloudNativePG Operator"

    echo "Installing CloudNativePG Operator..."
    kubectl apply --server-side -f \
        https://raw.githubusercontent.com/cloudnative-pg/cloudnative-pg/release-1.27/releases/cnpg-1.27.0.yaml

    echo "Waiting for CloudNativePG controller to be ready..."
    kubectl rollout status deployment \
        -n cnpg-system cnpg-controller-manager

    gum style --foreground 46 --bold "✓ CloudNativePG Operator deployment completed!"

    gum style --foreground 240 "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

deploy_arc() {
    gum style --foreground 129 --border-foreground 129 --border double --align center --width 50 --margin "1 2" --padding "2 4" "Deploying GitHub Actions Runner Controller"

    # Create namespaces
    echo "Creating ARC namespaces..."
    kubectl create namespace arc-systems || true
    kubectl create namespace arc-runners || true

    # Install ARC Controller first
    echo "Installing ARC Controller..."
    helm install arc \
        --namespace arc-systems \
        --create-namespace \
        oci://ghcr.io/actions/actions-runner-controller-charts/gha-runner-scale-set-controller || true

    echo "Waiting for ARC Controller to be ready..."
    kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=gha-rs-controller -n arc-systems --timeout=300s

    # Install ARC Runners
    echo "Installing ARC Runner Scale Set..."
    helm install arc-runner-set \
        --namespace arc-runners \
        --create-namespace \
        -f k8s/arc-configuration/gha-runner-scale-set/custom-values.yaml \
        oci://ghcr.io/actions/actions-runner-controller-charts/gha-runner-scale-set

    kubectl apply -f k8s/arc-configuration/gha-runner-scale-set/github-runner-role.yaml

    echo "Waiting for ARC Runner Scale Set to be ready..."
    kubectl wait --for=condition=ready pod -l app.kubernetes.io/component=runner-scale-set -n arc-runners --timeout=300s || true

    gum style --foreground 46 --bold "✓ GitHub Actions Runner Controller deployment completed!"

    gum style --foreground 240 "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

check_argocd_status() {
    gum style --foreground 51 --border-foreground 51 --border double --align center --width 50 --margin "1 2" --padding "2 4" "Checking ArgoCD Application Status"

    # Check if ArgoCD is running
    if ! kubectl get namespace argocd &>/dev/null; then
        gum style --foreground 196 --bold "❌ ArgoCD namespace not found - ArgoCD not deployed"
        return 1
    fi

    echo "Checking ArgoCD application controller status..."
    
    # Get application controller logs (last 100 lines)
    CONTROLLER_LOGS=$(kubectl logs -n argocd --tail=100 statefulset/argocd-application-controller 2>/dev/null || echo "No logs available")
    
    # Get all applications and their status
    echo "Analyzing ArgoCD applications..."
    APPS_STATUS=$(kubectl get applications -n argocd -o custom-columns=NAME:.metadata.name,HEALTH:.status.health.status,SYNC:.status.sync.status 2>/dev/null || echo "No applications found")
    
    # Count application states
    HEALTHY_COUNT=$(echo "$APPS_STATUS" | grep -c "Healthy" || echo "0")
    SYNCED_COUNT=$(echo "$APPS_STATUS" | grep -c "Synced" || echo "0")
    TOTAL_APPS=$(echo "$APPS_STATUS" | tail -n +2 | wc -l | tr -d ' ')
    
    # Analyze logs for common issues
    ERROR_COUNT=$(echo "$CONTROLLER_LOGS" | grep -i "error\|failed\|panic" | wc -l | tr -d ' ')
    SYNC_ERRORS=$(echo "$CONTROLLER_LOGS" | grep -i "sync.*error\|failed.*sync" | wc -l | tr -d ' ')
    PERMISSION_ERRORS=$(echo "$CONTROLLER_LOGS" | grep -i "permission\|forbidden\|unauthorized" | wc -l | tr -d ' ')
    
    # Display summary
    gum style --foreground 226 --bold "📊 ArgoCD Status Summary:"
    echo "Applications: $TOTAL_APPS total"
    echo "Healthy: $HEALTHY_COUNT | Synced: $SYNCED_COUNT"
    echo "Recent errors in logs: $ERROR_COUNT"
    echo "Sync errors: $SYNC_ERRORS"
    echo "Permission errors: $PERMISSION_ERRORS"
    
    echo ""
    gum style --foreground 75 --bold "Applications Status:"
    echo "$APPS_STATUS"
    
    # Issue identification
    echo ""
    if [ "$ERROR_COUNT" -gt 0 ]; then
        gum style --foreground 196 --bold "⚠ Issues Detected:"
        
        if [ "$SYNC_ERRORS" -gt 0 ]; then
            echo "- Sync errors found - check application manifests and repository access"
        fi
        
        if [ "$PERMISSION_ERRORS" -gt 0 ]; then
            echo "- Permission errors found - check RBAC and service account permissions"
        fi
        
        echo ""
        gum style --foreground 208 --bold "Recent error logs:"
        echo "$CONTROLLER_LOGS" | grep -i "error\|failed" | tail -5
        
        echo ""
        echo "💡 Troubleshooting commands:"
        echo "kubectl logs -n argocd statefulset/argocd-application-controller -f"
        echo "kubectl describe applications -n argocd"
        echo "argocd app list"
        echo "argocd app sync <app-name>"
    else
        gum style --foreground 46 --bold "✅ No critical issues detected in recent logs"
    fi

    gum style --foreground 240 "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

remove_metallb() {
    gum style --foreground 196 --border-foreground 196 --border double --align center --width 50 --margin "1 2" --padding "2 4" "Removing MetalLB K8s Resources"

    helm repo add metallb https://metallb.github.io/metallb || true
    
    kubectl delete -f k8s/metallb/ip-range.yaml || true

    kubectl delete -f https://raw.githubusercontent.com/metallb/metallb/v0.14.9/config/manifests/metallb-native.yaml || true
    
    kubectl delete -f k8s/metallb/metallb-namespace.yaml || true

    # Verify removal
    echo "Verifying MetalLB removal..."
    kubectl wait --for=delete namespace/metallb-system --timeout=120s || true
    
    if kubectl get namespace metallb-system &> /dev/null; then
        gum style --foreground 196 --bold "⚠ Warning: MetalLB namespace still exists"
    else
        gum style --foreground 46 --bold "✓ MetalLB successfully removed"
    fi

    gum style --foreground 240 "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

remove_democratic_csi() {
    gum style --foreground 166 --border-foreground 166 --border double --align center --width 50 --margin "1 2" --padding "2 4" "Removing Democratic CSI Resources"

    echo "Removing Democratic CSI resources..."
    kubectl delete -f k8s/csi/pvc.yaml || true
    kubectl delete -f k8s/csi/storageclass.yaml || true
    kubectl delete -f k8s/csi/all-resources-democratic-csi.yaml || true

    kubectl delete -f https://raw.githubusercontent.com/kubernetes-csi/external-snapshotter/v8.0.1/client/config/crd/snapshot.storage.k8s.io_volumesnapshotclasses.yaml | true
    kubectl delete -f https://raw.githubusercontent.com/kubernetes-csi/external-snapshotter/v8.0.1/client/config/crd/snapshot.storage.k8s.io_volumesnapshotcontents.yaml | true
    kubectl delete -f https://raw.githubusercontent.com/kubernetes-csi/external-snapshotter/v8.0.1/client/config/crd/snapshot.storage.k8s.io_volumesnapshots.yaml | true

    # Verify removal
    echo "Verifying Democratic CSI removal..."
    kubectl wait --for=delete namespace/democratic-csi --timeout=120s || true
    
    if kubectl get namespace democratic-csi &> /dev/null; then
        gum style --foreground 196 --bold "⚠ Warning: Democratic CSI namespace still exists"
        echo "Some resources may still be terminating. Check with: kubectl get all -n democratic-csi"
    else
        gum style --foreground 46 --bold "✓ Democratic CSI successfully removed"
    fi

    gum style --foreground 240 "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

remove_metallb() {
    gum style --foreground 196 --border-foreground 196 --border double --align center --width 50 --margin "1 2" --padding "2 4" "Removing MetalLB K8s Resources"

    helm repo add metallb https://metallb.github.io/metallb || true
    
    kubectl delete -f k8s/metallb/ip-range.yaml || true

    kubectl delete -f https://raw.githubusercontent.com/metallb/metallb/v0.14.9/config/manifests/metallb-native.yaml || true
    
    kubectl delete -f k8s/metallb/metallb-namespace.yaml || true

    # Verify removal
    echo "Verifying MetalLB removal..."
    kubectl wait --for=delete namespace/metallb-system --timeout=120s || true
    
    if kubectl get namespace metallb-system &> /dev/null; then
        gum style --foreground 196 --bold "⚠ Warning: MetalLB namespace still exists"
    else
        gum style --foreground 46 --bold "✓ MetalLB successfully removed"
    fi

    gum style --foreground 240 "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

remove_argocd() {
    gum style --foreground 208 --border-foreground 208 --border double --align center --width 50 --margin "1 2" --padding "2 4" "Removing ArgoCD K8s Resources"

    # Clean up app-of-apps and all ArgoCD applications
    echo "Cleaning up ArgoCD applications..."
    
    # First, remove finalizers to prevent hanging
    kubectl get applications -n argocd -o name 2>/dev/null | xargs -I {} kubectl patch {} -n argocd -p '{"metadata":{"finalizers":[]}}' --type=merge 2>/dev/null || true
    
    kubectl delete -f k8s/argocd/app-of-apps.yaml -n argocd || true
    kubectl delete applications --all -n argocd --timeout=60s || true

    kubectl delete -f k8s/argocd/argocd-ingress.yml -n argocd || true

    kubectl delete -f k8s/argocd/argocd-install.yaml -n argocd || true

    kubectl delete secret argocd-ssh-config -n argocd || true

    kubectl delete namespace argocd || true

    # Verify removal
    echo "Verifying ArgoCD removal..."
    kubectl wait --for=delete namespace/argocd --timeout=120s || true
    
    if kubectl get namespace argocd &> /dev/null; then
        gum style --foreground 196 --bold "⚠ Warning: ArgoCD namespace still exists"
        echo "Some resources may still be terminating. Check with: kubectl get all -n argocd"
    else
        gum style --foreground 46 --bold "✓ ArgoCD successfully removed"
    fi

    gum style --foreground 240 "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

remove_prometheus_operator() {
    gum style --foreground 178 --border-foreground 178 --border double --align center --width 50 --margin "1 2" --padding "2 4" "Removing Prometheus Operator CRDs"

    echo "Removing Prometheus Operator CRDs..."
    kubectl delete crd servicemonitors.monitoring.coreos.com || true
    kubectl delete crd prometheuses.monitoring.coreos.com || true
    kubectl delete crd alertmanagers.monitoring.coreos.com || true
    kubectl delete crd prometheusrules.monitoring.coreos.com || true
    kubectl delete crd podmonitors.monitoring.coreos.com || true

    # Verify removal
    echo "Verifying CRD removal..."
    if kubectl get crd servicemonitors.monitoring.coreos.com &> /dev/null; then
        gum style --foreground 196 --bold "⚠ Warning: Some Prometheus CRDs still exist"
    else
        gum style --foreground 46 --bold "✓ Prometheus Operator CRDs successfully removed"
    fi

    gum style --foreground 240 "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

remove_cnpg_operator() {
    gum style --foreground 201 --border-foreground 201 --border double --align center --width 50 --margin "1 2" --padding "2 4" "Removing CloudNativePG Operator"

    echo "Removing CloudNativePG Operator..."
    kubectl delete -f \
        https://raw.githubusercontent.com/cloudnative-pg/cloudnative-pg/release-1.27/releases/cnpg-1.27.0.yaml || true

    echo "Removing CloudNativePG namespace..."
    kubectl delete namespace cnpg-system || true

    # Verify removal
    echo "Verifying CloudNativePG removal..."
    kubectl wait --for=delete namespace/cnpg-system --timeout=120s || true
    
    if kubectl get namespace cnpg-system &> /dev/null; then
        gum style --foreground 196 --bold "⚠ Warning: CloudNativePG namespace still exists"
        echo "Some resources may still be terminating. Check with: kubectl get all -n cnpg-system"
    else
        gum style --foreground 46 --bold "✓ CloudNativePG Operator successfully removed"
    fi

    gum style --foreground 240 "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

remove_arc() {
    gum style --foreground 160 --border-foreground 160 --border double --align center --width 50 --margin "1 2" --padding "2 4" "Removing GitHub Actions Runner Controller"

    echo "Removing ARC Runner Scale Set..."
    helm uninstall arc-runner-set -n arc-runners || true

    echo "Removing ARC Controller..."
    helm uninstall arc -n arc-systems || true

    echo "Removing ARC namespaces..."
    kubectl delete namespace arc-runners || true
    kubectl delete namespace arc-systems || true

    # Verify removal
    echo "Verifying ARC removal..."
    if kubectl get namespace arc-systems &> /dev/null || kubectl get namespace arc-runners &> /dev/null; then
        gum style --foreground 196 --bold "⚠ Warning: Some ARC namespaces still exist"
        echo "Check with: kubectl get all -n arc-systems && kubectl get all -n arc-runners"
    else
        gum style --foreground 46 --bold "✓ GitHub Actions Runner Controller successfully removed"
    fi

    gum style --foreground 240 "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

# Check for --uninstall flag
if [[ "$1" == "--uninstall" ]]; then
    echo "Select resources to uninstall:"
    resources=$(gum choose --no-limit remove_arc remove_argocd remove_cnpg_operator remove_prometheus_operator remove_metallb remove_democratic_csi)
    
    for resource in ${resources}
    do 
        eval $resource
    done
    
    gum confirm "Uninstall completed. Select Yes to end here... Or Select No to continue to new deployment" && exit 0 
fi

resources=$(gum choose --no-limit setup_node deploy_democratic_csi deploy_metallb deploy_prometheus_operator deploy_cnpg_operator deploy_argocd check_argocd_status deploy_arc)

for resource in ${resources}
do 
    eval $resource
done
