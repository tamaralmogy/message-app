#!/bin/bash

# Define your stack name
STACK_NAME="dev"

# Login to Pulumi (if needed)
pulumi login

# Select the appropriate stack
pulumi stack select $STACK_NAME

# Preview the update to ensure everything looks good
pulumi preview

# Deploy the stack
pulumi up --yes

# Export the outputs to a file for reference
pulumi stack output > outputs.txt

# Optionally, destroy the stack if you want to clean up resources
# pulumi destroy --yes
