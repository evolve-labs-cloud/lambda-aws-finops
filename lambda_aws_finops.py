import boto3
from botocore.exceptions import ClientError
from datetime import datetime, timedelta
import os
import json
import urllib.request
import logging

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS Cost Explorer client
ce_client = boto3.client("ce")


def get_date_range():
    end_date = datetime.now().replace(day=1)
    start_date = end_date - timedelta(days=180)
    return start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")


def get_cost_data(start_date, end_date):
    try:
        response = ce_client.get_cost_and_usage(
            TimePeriod={"Start": start_date, "End": end_date},
            Granularity="MONTHLY",
            Metrics=["UnblendedCost"],
            GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
        )
        return response["ResultsByTime"]
    except ClientError as e:
        logger.error(f"An error occurred while fetching cost data: {e}")
        return None


def analyze_costs():
    start_date, end_date = get_date_range()
    cost_data = get_cost_data(start_date, end_date)

    if not cost_data:
        return None, None, None, None

    # Process data
    monthly_costs = {}
    for month_data in cost_data:
        month = datetime.strptime(
            month_data["TimePeriod"]["Start"], "%Y-%m-%d"
        ).strftime("%Y-%m")
        monthly_costs[month] = {
            item["Keys"][0]: float(item["Metrics"]["UnblendedCost"]["Amount"])
            for item in month_data["Groups"]
        }

    # Get the current and previous month
    months = sorted(monthly_costs.keys())
    current_month, previous_month = months[-1], months[-2]

    # Get top 10 services for current month
    current_top_10 = sorted(
        monthly_costs[current_month].items(), key=lambda x: x[1], reverse=True
    )[:10]

    # Create a comparison dictionary
    top_10_comparison = {}
    for service, current_cost in current_top_10:
        previous_cost = monthly_costs[previous_month].get(service, 0)
        change = current_cost - previous_cost
        percent_change = (
            (change / previous_cost * 100) if previous_cost > 0 else float("inf")
        )
        top_10_comparison[service] = {
            "current": current_cost,
            "previous": previous_cost,
            "change": change,
            "percent_change": percent_change,
        }

    return top_10_comparison, monthly_costs, current_month, previous_month


def create_ascii_chart(monthly_costs):
    months = sorted(monthly_costs.keys())
    total_costs = [sum(monthly_costs[month].values()) for month in months]

    max_cost = max(total_costs)
    chart_width = 20
    chart = "6-Month Cost Overview\n\n"

    for month, cost in zip(months, total_costs):
        bar_length = int((cost / max_cost) * chart_width)
        bar = "█" * bar_length
        chart += f"{month}: ${cost:.2f}\n"
        chart += f"{bar.ljust(chart_width)} | {cost:.2f}\n\n"

    return chart


def create_report(top_10_comparison, monthly_costs, current_month, previous_month):
    ascii_chart = create_ascii_chart(monthly_costs)

    report = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"AWS Cost Analysis: {current_month} vs {previous_month}",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*Top 10 Most Expensive Services Comparison:*",
            },
        },
    ]

    for service, data in top_10_comparison.items():
        change_icon = (
            "🔼" if data["change"] > 0 else "🔽" if data["change"] < 0 else "➖"
        )
        report.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    f"text": f"*{service}*\n"
                    f"Current: ${data['current']:.2f}\n"
                    f"Previous: ${data['previous']:.2f}\n"
                    f"Change: {change_icon} ${abs(data['change']):.2f} ({data['percent_change']:.2f}%)",
                },
            }
        )

    report.extend(
        [
            {"type": "divider"},
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "6-Month Cost Overview"},
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"```\n{ascii_chart}\n```"},
            },
        ]
    )

    return report


def send_to_slack(report):
    slack_webhook_url = os.environ.get("SLACK_WEBHOOK_URL")

    if not slack_webhook_url:
        logger.error("SLACK_WEBHOOK_URL environment variable is not set")
        return None

    data = {"blocks": report}

    req = urllib.request.Request(
        slack_webhook_url,
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )

    try:
        with urllib.request.urlopen(req) as response:
            if response.getcode() != 200:
                logger.error(
                    f"Slack API returned non-200 status code: {response.getcode()}"
                )
                return None
            return response.read()
    except Exception as e:
        logger.error(f"Error sending message to Slack: {str(e)}")
        return None


def lambda_handler(event, context):
    try:
        top_10_comparison, monthly_costs, current_month, previous_month = (
            analyze_costs()
        )

        if not top_10_comparison:
            logger.error("Error fetching cost data")
            return {"statusCode": 500, "body": json.dumps("Error fetching cost data")}

        report = create_report(
            top_10_comparison, monthly_costs, current_month, previous_month
        )
        slack_response = send_to_slack(report)

        if slack_response:
            logger.info("Report sent to Slack successfully")
            return {
                "statusCode": 200,
                "body": json.dumps("Report sent to Slack successfully"),
            }
        else:
            logger.error("Failed to send report to Slack")
            return {
                "statusCode": 500,
                "body": json.dumps("Error sending report to Slack"),
            }
    except Exception as e:
        logger.error(f"Unexpected error in lambda_handler: {str(e)}")
        return {"statusCode": 500, "body": json.dumps(f"Unexpected error: {str(e)}")}
