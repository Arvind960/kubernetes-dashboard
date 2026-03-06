#!/bin/bash
# Delete all CloudWatch metrics from ContainerInsights namespace

REGION="ap-south-1"
NAMESPACE="ContainerInsights"

echo "🗑️  Deleting CloudWatch metrics from namespace: $NAMESPACE"
echo ""

# Get all unique metric names
METRICS=$(aws cloudwatch list-metrics \
  --namespace $NAMESPACE \
  --region $REGION \
  --query 'Metrics[*].MetricName' \
  --output text | tr '\t' '\n' | sort -u)

echo "Found metrics to delete:"
echo "$METRICS"
echo ""

# Note: CloudWatch doesn't have a direct delete API for metrics
# Metrics expire automatically after 15 months of no new data
# We'll stop the exporter to prevent new metrics

echo "⚠️  Note: CloudWatch metrics cannot be directly deleted via API"
echo "They will expire after 15 months of inactivity"
echo ""
echo "Stopping CloudWatch exporter to prevent new metrics..."

# Stop the CloudWatch exporter
pkill -f k8s_cloudwatch_exporter

if [ $? -eq 0 ]; then
    echo "✅ CloudWatch exporter stopped"
else
    echo "ℹ️  CloudWatch exporter was not running"
fi

echo ""
echo "To manually delete metrics in AWS Console:"
echo "1. Go to: https://ap-south-1.console.aws.amazon.com/cloudwatch/"
echo "2. Navigate to Metrics → All metrics"
echo "3. Select 'ContainerInsights' namespace"
echo "4. Metrics will stop appearing after 2 weeks of no data"
