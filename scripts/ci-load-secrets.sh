#!/bin/bash

# Define your Azure Key Vault name
KEY_VAULT_NAME="${AZURE_KEY_VAULT_NAME}"

# Function to retrieve a secret, translate the name, and load it into the environment
get_secret() {
  local SECRET_NAME=$1
  local SECRET_VALUE=$(az keyvault secret show --name $SECRET_NAME --vault-name $KEY_VAULT_NAME --query value -o tsv)

  if [ $? -ne 0 ]; then
    echo "Error retrieving secret: $SECRET_NAME"
    exit 1
  fi

  # Convert SECRET_NAME by replacing dashes with underscores, keeping the case as is
  local ENV_NAME=$(echo $SECRET_NAME | tr '-' '_')

  # Export the secret as an environment variable
  export $ENV_NAME="$SECRET_VALUE"
}

# Fetch all secret names from the Key Vault
SECRET_NAMES=$(az keyvault secret list --vault-name $KEY_VAULT_NAME --query "[].name" -o tsv)

# Loop through the secret names and load each one into the environment
for SECRET_NAME in $SECRET_NAMES; do
  get_secret $SECRET_NAME
done

echo "All secrets have been loaded into the environment."
# Verify by printing the value of the 'DEBUG' environment variable
echo "SECRET environment variable value: $SECRET_KEY"
