#!/bin/bash

# Define your Azure Key Vault name
KEY_VAULT_NAME="Majibu-Github-Secrets"

# Define the output .env file
ENV_FILE=".env"

# Start with an empty .env file
> $ENV_FILE

# Function to retrieve a secret and append it to the .env file
get_secret() {
  local SECRET_NAME=$1
  local SECRET_VALUE=$(az keyvault secret show --name $SECRET_NAME --vault-name $KEY_VAULT_NAME --query value -o tsv)

  if [ $? -ne 0 ]; then
    echo "Error retrieving secret: $SECRET_NAME"
    exit 1
  fi

  echo "$SECRET_NAME=$SECRET_VALUE" >> $ENV_FILE
}

# Fetch all secret names from the Key Vault
SECRET_NAMES=$(az keyvault secret list --vault-name $KEY_VAULT_NAME --query "[].name" -o tsv)

# Loop through the secret names and get each one
for SECRET_NAME in $SECRET_NAMES; do
  get_secret $SECRET_NAME
done

echo "All secrets loaded into $ENV_FILE successfully."
