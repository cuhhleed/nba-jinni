{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "lambda:UpdateFunctionCode",
        "lambda:GetFunction",
        "lambda:InvokeFunction"
      ],
      "Resource": "arn:aws:lambda:${aws_region}:${account_id}:function:${project_name}-${environment}-*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject",
        "s3:ListBucket",
        "s3:GetBucketLocation"
      ],
      "Resource": [
        "arn:aws:s3:::${project_name}-${environment}-frontend",
        "arn:aws:s3:::${project_name}-${environment}-frontend/*",
        "arn:aws:s3:::${project_name}-${environment}-data-exports",
        "arn:aws:s3:::${project_name}-${environment}-data-exports/*",
        "arn:aws:s3:::${project_name}-${environment}-lambda-artifacts",
        "arn:aws:s3:::${project_name}-${environment}-lambda-artifacts/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "cloudfront:CreateInvalidation",
        "cloudfront:GetInvalidation",
        "cloudfront:GetDistribution",
        "cloudfront:ListDistributions"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue",
        "secretsmanager:DescribeSecret"
      ],
      "Resource": "arn:aws:secretsmanager:${aws_region}:${account_id}:secret:${project_name}/${environment}/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "rds:DescribeDBInstances"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:DescribeLogGroups",
        "logs:DescribeLogStreams",
        "logs:GetLogEvents",
        "logs:FilterLogEvents"
      ],
      "Resource": "arn:aws:logs:${aws_region}:${account_id}:log-group:/aws/lambda/${project_name}-${environment}-*:*"
    }
  ]
}
