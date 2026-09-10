"""AWS Cost Guardrail Setup Script.

Creates:
1. A hard $100.00 USD monthly AWS Cost Budget scoped to Amazon Bedrock.
2. Tiered alert thresholds:
   - 50% ($50) Actual Spend -> Notification to Team
   - 80% ($80) Actual Spend -> Warning Notification
   - 100% ($100) Actual Spend -> Critical Alert
"""

import sys
import boto3
from botocore.exceptions import ClientError


def setup_bedrock_budget(
    account_id: str,
    notification_email: str,
    monthly_amount: float = 100.0,
    region: str = "ap-southeast-1"
):
    print(f"Creating AWS Budget of ${monthly_amount:.2f}/month for Bedrock in account {account_id}...")
    budgets_client = boto3.client("budgets", region_name=region)

    budget_name = "SalesCoachAI-Bedrock-100USD-Monthly-Budget"

    budget_definition = {
        "BudgetName": budget_name,
        "BudgetLimit": {
            "Amount": str(monthly_amount),
            "Unit": "USD"
        },
        "CostFilters": {
            "Service": ["Amazon Bedrock", "bedrock"]
        },
        "CostTypes": {
            "IncludeTax": True,
            "IncludeSubscription": True,
            "UseBlended": False,
            "IncludeRefund": False,
            "IncludeCredit": False,
            "IncludeUpfront": True,
            "IncludeRecurring": True,
            "IncludeOtherSubscription": True,
            "IncludeSupport": False,
            "IncludeDiscount": True,
            "UseAmortized": False
        },
        "TimeUnit": "MONTHLY",
        "BudgetType": "COST"
    }

    notifications_with_subscribers = [
        {
            "Notification": {
                "NotificationType": "ACTUAL",
                "ComparisonOperator": "GREATER_THAN",
                "Threshold": 50.0,
                "ThresholdType": "PERCENTAGE",
                "NotificationState": "ALARM"
            },
            "Subscribers": [
                {
                    "SubscriptionType": "EMAIL",
                    "Address": notification_email
                }
            ]
        },
        {
            "Notification": {
                "NotificationType": "ACTUAL",
                "ComparisonOperator": "GREATER_THAN",
                "Threshold": 80.0,
                "ThresholdType": "PERCENTAGE",
                "NotificationState": "ALARM"
            },
            "Subscribers": [
                {
                    "SubscriptionType": "EMAIL",
                    "Address": notification_email
                }
            ]
        },
        {
            "Notification": {
                "NotificationType": "ACTUAL",
                "ComparisonOperator": "GREATER_THAN",
                "Threshold": 100.0,
                "ThresholdType": "PERCENTAGE",
                "NotificationState": "ALARM"
            },
            "Subscribers": [
                {
                    "SubscriptionType": "EMAIL",
                    "Address": notification_email
                }
            ]
        }
    ]

    try:
        budgets_client.create_budget(
            AccountId=account_id,
            Budget=budget_definition,
            NotificationsWithSubscribers=notifications_with_subscribers
        )
        print(f"✅ Successfully created AWS Budget: {budget_name}")
    except ClientError as e:
        if e.response.get("Error", {}).get("Code") == "DuplicateRecordException":
            print(f"ℹ️ Budget '{budget_name}' already exists. Updating existing budget...")
            budgets_client.update_budget(
                AccountId=account_id,
                NewBudget=budget_definition
            )
            print(f"✅ Successfully updated AWS Budget: {budget_name}")
        else:
            print(f"❌ Failed to create AWS Budget: {e}")
            raise


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python setup_aws_cost_guardrails.py <AWS_ACCOUNT_ID> <NOTIFICATION_EMAIL> [MONTHLY_BUDGET_USD]")
        print("Example: python setup_aws_cost_guardrails.py 123456789012 devops@example.com 100.0")
        sys.exit(1)

    acc_id = sys.argv[1]
    email = sys.argv[2]
    amount = float(sys.argv[3]) if len(sys.argv) > 3 else 100.0

    setup_bedrock_budget(acc_id, email, amount)
