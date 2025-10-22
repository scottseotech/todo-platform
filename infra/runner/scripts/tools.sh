#!/bin/bash

echo ------------------------------------------------------------------------
echo installing helm kubectl kustomize argocd gh yq python poetry
echo ------------------------------------------------------------------------


curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash


curl -sSLO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -m 555 kubectl /usr/local/bin/kubectl
rm kubectl


curl -sS "https://raw.githubusercontent.com/kubernetes-sigs/kustomize/master/hack/install_kustomize.sh"  | bash
sudo install -m 555 kustomize /usr/local/bin/kustomize
rm kustomize


curl -sSL -o argocd-linux-amd64 https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64
sudo install -m 555 argocd-linux-amd64 /usr/local/bin/argocd
rm argocd-linux-amd64


(
  set -x; cd "$(mktemp -d)" &&
  OS="$(uname | tr '[:upper:]' '[:lower:]')" &&
  ARCH="$(uname -m | sed -e 's/x86_64/amd64/' -e 's/\(arm\)\(64\)\?.*/\1\2/' -e 's/aarch64$/arm64/')" &&
  KREW="krew-${OS}_${ARCH}" &&
  curl -fsSLO "https://github.com/kubernetes-sigs/krew/releases/latest/download/${KREW}.tar.gz" &&
  tar zxvf "${KREW}.tar.gz" &&
  ./"${KREW}" install krew
)
export PATH="${KREW_ROOT:-$HOME/.krew}/bin:$PATH"
kubectl krew install whoami
kubectl krew install oidc-login
kubectl krew install ctx


(type -p wget >/dev/null || (sudo apt update && sudo apt-get install wget -y)) \
	&& sudo mkdir -p -m 755 /etc/apt/keyrings \
        && out=$(mktemp) && wget -nv -O$out https://cli.github.com/packages/githubcli-archive-keyring.gpg \
        && cat $out | sudo tee /etc/apt/keyrings/githubcli-archive-keyring.gpg > /dev/null \
	&& sudo chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg \
	&& echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null \
	&& sudo apt update \
	&& sudo apt install gh -y


VERSION=v4.2.0
BINARY=yq_linux_amd64
curl -sSL -o ${BINARY} https://github.com/mikefarah/yq/releases/download/${VERSION}/${BINARY}
sudo install -m 555 ${BINARY} /usr/local/bin/yq
rm ${BINARY}

echo ------------------------------------------------------------------------
echo installing golang and its tool chain
echo ------------------------------------------------------------------------

curl -sSL -o go1.25.3.linux-amd64.tar.gz https://go.dev/dl/go1.25.3.linux-amd64.tar.gz
sudo tar -C /usr/local -xzf go1.25.3.linux-amd64.tar.gz
rm go1.25.3.linux-amd64.tar.gz
export PATH="$PATH:/usr/local/go/bin"

echo ------------------------------------------------------------------------
echo installing python and poetry
echo ------------------------------------------------------------------------

# Install Python 3.11.9
sudo apt-get update
sudo apt-get install -y python3.11 python3.11-venv python3.11-dev python3-pip python3.11-distutils

# Create symlinks for consistency
sudo ln -sf /usr/bin/python3.11 /usr/local/bin/python
sudo ln -sf /usr/bin/python3.11 /usr/local/bin/python3

# Install Poetry
echo "📚 Installing Poetry..."
curl -sSL https://install.python-poetry.org | python3 -

# Add Poetry to PATH for current session
export PATH="$HOME/.local/bin:$PATH"

# Configure Poetry to create venvs in project directory
$HOME/.local/bin/poetry config virtualenvs.in-project true

echo "✅ Python $(python --version) and Poetry installed successfully"

# Download and install mc client
curl -fsSL https://dl.min.io/client/mc/release/linux-amd64/mc -o mc
chmod +x mc
sudo mv mc /usr/local/bin/

# Verify installation
mc --version