![workflow](https://github.com/ei-roslyakov/aws_bill_report/actions/workflows/tests.yml/badge.svg)
![workflow](https://github.com/ei-roslyakov/aws_bill_report/actions/workflows/deploy.yml/badge.svg)
## Script for getting billing data from AWS Cost Explorer  
## How to use  
### Install dependencies

```python
pip3 install -r requirements.txt 
```
### To use
```python
python3 ./get_bill.py
```

### Script arguments
| Name         | Description                                       | Default    |
|--------------|---------------------------------------------------|------------|
| `--profile`  | AWS profile to get access to assume role  | default    |
| `--month`    | The report will be created for this month         | current   |
| `--year`     | The report will be created for this year          | current |
| `--sns-topic-arn`     | The S3 bucket to save the report          | OS env SNS_TOPIC_ARN default: ""|
| `--bucket-name`     | The S3 bucket to save the report          | OS env S3_BUCKET_NAME default: rei-data|
| `--bucket-key`     | The S3 bucket key to save the report          | OS env S3_BUCKET_KEY default: bill_report|
| `--table-name`     | The DynamoDB table name to save data         | OS env DYNAMODB_TABLE default: SU-bill|
