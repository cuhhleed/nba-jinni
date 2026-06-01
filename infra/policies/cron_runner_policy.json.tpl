{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": "cloudwatch:PutMetricData",
            "Resource": "*",
            "Condition": {
                "StringEquals": {
                    "cloudwatch:namespace": "NBAJinni/Ingestion"
                }
            }
        },
        {
            "Effect": "Allow",
            "Action": "s3:PutObject",
            "Resource": "${bucket_arn}/exports/*"
        },
        {
            "Effect": "Allow",
            "Action": "lambda:InvokeFunction",
            "Resource": "${loader_lambda_arn}"
        }
    ]
}
