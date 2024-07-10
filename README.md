# Message App

A simple messaging application built with AWS Lambda, DynamoDB, and API Gateway.

## Features

- **Register a new user**: Generates a new user ID.
- **Send a message to a user**: Messages are sent from one user to another by their user ID.
- **Block a user**: Allows a user to block another user from sending messages to them.
- **Create a group**: Creates a new group with a unique ID.
- **Add / remove users from a group**: Manage group members.
- **Send messages to a group**: Messages can be sent to all members of a group.
- **Check messages**: Users can check for their messages.

## Endpoints

### User Management
- **Register User**: `POST /register`
- **Block User**: `POST /block`

### Messaging
- **Send Message**: `POST /message`
- **Check Messages**: `POST /messages`

### Group Management
- **Create Group**: `POST /group`
- **Add User to Group**: `POST /group/add-user`
- **Remove User from Group**: `POST /group/remove-user`
- **Send Group Message**: `POST /group/message`

## Scaling Discussion

### At 1000s of Users
- **Load**: The system should handle this with minimal latency using AWS Lambda's auto-scaling capabilities. DynamoDB's on-demand capacity mode ensures that the database can handle spikes in traffic.
- **Cost**: Costs will be primarily based on the number of requests to AWS Lambda and DynamoDB. The AWS free tier provides significant leeway, but monitoring usage is still important.

### At 10,000s of Users
- **Load**: AWS Lambda's auto-scaling will continue to manage the increased load. DynamoDB read/write capacity will need to be monitored and potentially increased.
- **Cost**: Costs will rise due to increased Lambda invocations and higher DynamoDB throughput. Using AWS Cost Explorer and budgeting tools can help manage and predict costs.

### At Millions of Users
- **Load**: The system may need architectural adjustments. Implementing caching with Amazon ElastiCache, using Amazon SQS for queuing, and optimizing Lambda functions will be necessary.
- **Cost**: Costs will be significant. Using DynamoDB's reserved capacity pricing, optimizing resource usage, and leveraging AWS Savings Plans can help manage expenses.

## Deployment

### Pulumi Script

You can deploy this application using Pulumi. Ensure Pulumi and AWS CLI are configured on your machine.

1. **Configure Pulumi:**
    ```sh
    pulumi config set aws:region YOUR_AWS_REGION
    ```

2. **Deploy the application:**
    ```sh
    pulumi up
    ```

## Getting Started

### Prerequisites
- [Pulumi](https://www.pulumi.com/docs/get-started/install/)
- [AWS CLI](https://aws.amazon.com/cli/)

### Installation
1. **Clone the repository:**
    ```sh
    git clone https://github.com/tamaralmogy/message-app.git
    cd message-app
    ```

2. **Install dependencies:**
    ```sh
    pip install -r requirements.txt
    ```

3. **Deploy the application:**
    ```sh
    pulumi up
    ```

## Repository

The project repository is hosted on GitHub: [Message App](https://github.com/tamaralmogy/message-app)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
