# AWS Cost Analysis Slack Notifications

This AWS Lambda function analyzes AWS cost data over a 6-month period and sends detailed cost analysis reports to Slack. It provides insights into service-wise cost comparisons, trends, and visualizations.

## Features

- 📊 Monthly cost analysis and comparison
- 🔝 Top 10 most expensive AWS services tracking
- 📈 6-month cost overview with ASCII chart visualization
- ↕️ Month-over-month cost change analysis
- 🔔 Automated Slack notifications
- 📅 Rolling 6-month historical data analysis

## Prerequisites

- AWS Account with Cost Explorer API access
- Slack workspace with incoming webhook configuration
- AWS Lambda execution role with appropriate permissions
- Python 3.x runtime environment

## Environment Variables

| Variable            | Description                | Required |
| ------------------- | -------------------------- | -------- |
| `SLACK_WEBHOOK_URL` | Slack incoming webhook URL | Yes      |

## Function Capabilities

### Cost Analysis

- Tracks costs over a 6-month period
- Compares current month with previous month
- Identifies top 10 most expensive services
- Calculates month-over-month changes
- Generates cost trend visualizations

### Slack Notifications

- Formatted message blocks for better readability
- Service-wise cost comparison
- Trend indicators (🔼 increase, 🔽 decrease, ➖ no change)
- ASCII chart for visual trend analysis
- Percentage change calculations

## Setup Instructions

1. **Configure Slack Webhook:**

   - Go to your Slack workspace
   - Create an incoming webhook
   - Copy the webhook URL

2. **Deploy Lambda Function:**

   - Create a new Lambda function using Python 3.x runtime
   - Copy the provided code
   - Set the `SLACK_WEBHOOK_URL` environment variable
   - Configure appropriate timeout (recommended: 1 minute)
   - Set memory based on your data volume (recommended: 256MB)

3. **Configure IAM Permissions:**
   - Attach the following policy to your Lambda execution role:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["ce:GetCostAndUsage"],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    }
  ]
}
```

4. **Set Up Trigger:**
   - Configure EventBridge (CloudWatch Events) rule
   - Recommended schedule: Rate(1 day) or cron expression
   - Target: Your Lambda function

## Report Format

The Slack notification includes:

1. **Header**

   - Analysis period (Current month vs Previous month)

2. **Top 10 Services Comparison**

   - Service name
   - Current month cost
   - Previous month cost
   - Cost change (absolute and percentage)
   - Trend indicator

3. **Cost Overview**
   - ASCII chart showing 6-month cost trend
   - Monthly total costs

## Error Handling

The function includes comprehensive error handling for:

- Cost Explorer API failures
- Invalid date ranges
- Slack API communication issues
- Data processing errors

All errors are logged to CloudWatch Logs for debugging.

## Monitoring

Monitor the function using:

- CloudWatch Logs for execution logs
- CloudWatch Metrics for invocation statistics
- Lambda function metrics for performance data

## Troubleshooting

Common issues and solutions:

### 1. No Cost Data

- Verify Cost Explorer API access
- Check IAM permissions
- Ensure the account has cost data available

### 2. Slack Notification Failures

- Verify webhook URL is correct
- Check network connectivity
- Validate Slack message format

### 3. Function Timeouts

- Increase Lambda timeout value
- Optimize data processing
- Check Cost Explorer API response times

## Customization

You can customize the function by:

- Modifying the analysis period in `get_date_range()`
- Adjusting the number of top services in `analyze_costs()`
- Customizing the ASCII chart in `create_ascii_chart()`
- Modifying the Slack message format in `create_report()`

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- AWS Cost Explorer Documentation
- Slack API Documentation
- AWS Lambda Documentation
