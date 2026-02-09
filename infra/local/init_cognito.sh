#!/bin/bash
echo "Initializing Cognito..."

# 1. Create the User Pool
awslocal cognito-idp create-user-pool --pool-name my-test-pool

# 2. Create the App Client
# Note: In LocalStack, you can sometimes force specific IDs, or you simply capture 
# the output. For simplicity here, we assume standard generation. 
# If you need a fixed ID for your .env file, LocalStack Pro supports deterministic IDs, 
# but for Community, we usually just grep the ID or query it dynamically.

# Let's create a client and specific user for testing
awslocal cognito-idp create-user-pool-client \
    --user-pool-id us-east-1_my-test-pool \
    --client-name my-test-client

# 3. Create a dummy user
awslocal cognito-idp admin-create-user \
    --user-pool-id us-east-1_my-test-pool \
    --username testuser@example.com \
    --user-attributes Name=email,Value=testuser@example.com

# 4. Set the user password (so you can login immediately)
awslocal cognito-idp admin-set-user-password \
    --user-pool-id us-east-1_my-test-pool \
    --username testuser@example.com \
    --password "Password123!" \
    --permanent

echo "Cognito initialized."