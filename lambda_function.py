import argparse
import os.path

import boto3

from botocore.exceptions import ClientError

import loguru

import pandas as pd

import datetime

logger = loguru.logger


def parse_args():
    parsers = argparse.ArgumentParser()

    parsers.add_argument(
        "--profile",
        required=False,
        type=str,
        default=os.environ.get("AWS_PROFILE", "default"),
        action="store",
        help="AWS Profile",
    )
    parsers.add_argument(
        "--region",
        required=False,
        type=str,
        default=os.environ.get("AWS_REGION", "eu-west-2"),
        action="store",
        help="AWS region",
    )
    parsers.add_argument(
        "--bucket-name",
        required=False,
        type=str,
        default=os.environ.get("S3_BUCKET_NAME", "rei-data"),
        action="store",
        help="S3 bucket to save the report",
    )
    parsers.add_argument(
        "--bucket-key",
        required=False,
        type=str,
        default=os.environ.get("S3_BUCKET_KEY", "bill_report"),
        action="store",
        help="S3 bucket key to save the report",
    )
    parsers.add_argument(
        "--sns-topic-arn",
        required=False,
        type=str,
        default=os.environ.get("SNS_TOPIC_ARN", ""),
        action="store",
        help="SNS topic AEN to send notification",
    )
    parsers.add_argument(
        "--table-name",
        required=False,
        type=str,
        default=os.environ.get("DYNAMODB_TABLE", "su-bill-report"),
        action="store",
        help="The DynamoDB table name to save data",
    )
    parsers.add_argument(
        "--rep-path",
        required=False,
        type=str,
        default=os.environ.get("REPORT_PATH", "/tmp"),
        action="store",
        help="The path to save the exel report",
    )
    parsers.add_argument(
        "--month",
        required=False,
        type=int,
        default=datetime.datetime.now().strftime("%m"),
        action="store",
        help="Month",
    )
    parsers.add_argument(
        "--year",
        required=False,
        type=str,
        default=datetime.datetime.now().strftime("%Y"),
        action="store",
        help="The beginning of the time period",
    )

    return parsers.parse_args()


def client_role(acc_id: str, region: str):

    sts_client = boto3.client("sts")
    assumed_role = sts_client.assume_role(
        RoleArn=f"arn:aws:iam::{acc_id}:role/su-get-bill-data-access",
        RoleSessionName="AssumeRoleSession1",
        DurationSeconds=1800,
    )
    session = boto3.Session(
        aws_access_key_id=assumed_role["Credentials"]["AccessKeyId"],
        aws_secret_access_key=assumed_role["Credentials"]["SecretAccessKey"],
        aws_session_token=assumed_role["Credentials"]["SessionToken"],
        region_name=region,
    )
    ce_client = session.client("ce")

    return ce_client


def dynamodb_client():

    dynamodb_client = boto3.client("dynamodb")

    return dynamodb_client


def s3_client():

    s3_client = boto3.client("s3")

    return s3_client


def sns_client():

    sns_client = boto3.client("sns")

    return sns_client


def dynamodb_resource():

    dynamodb_resource = boto3.resource("dynamodb")

    return dynamodb_resource


def get_bill_by_period(ce_client, start: str, end: str, project="NoN") -> list:

    logger.info(f"{project}: Getting data for period {start} - {end}")
    try:
        response = ce_client.get_cost_and_usage(
            TimePeriod={"Start": start, "End": end},
            Granularity="MONTHLY",
            Metrics=["BlendedCost"],
        )
        return response
    except ClientError as e:
        logger.exception(f"Something went wrong {e.response['Error']['Message']}")


def get_date_range(year: str, month: str):
    suitable_value_for_month = [*range(1, 13)]

    if month not in suitable_value_for_month:
        logger.exception(
            f"You have provided the wrong month number {month}, available values are {suitable_value_for_month} "
        )
        exit(1)
    start = None
    end = None

    if month == "12":
        start = f"{year}-{'%0.2d' % int(month)}-01"
        end = f"{int(year) + 1}-01-01"
    else:
        start = start = f"{year}-{'%0.2d' % int(month)}-01"
        end = f"{year}-{'%0.2d' % (int(month) + 1)}-01"

    return {"start": start, "end": end}


def check_table_exists(resource, table_name: str) -> bool:
    try:
        resource.Table(table_name).table_status
    except resource.meta.client.exceptions.ResourceNotFoundException:
        return False
    return True


def create_table(dynamodb, table_name: str):
    try:
        response = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {"AttributeName": "Project", "KeyType": "HASH"},
                {"AttributeName": "Id", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "Project", "AttributeType": "S"},
                {"AttributeName": "Id", "AttributeType": "S"},
            ],
            ProvisionedThroughput={"ReadCapacityUnits": 1, "WriteCapacityUnits": 1},
        )
        logger.info("CREATED")
        return response
    except ClientError as err:
        logger.error(
            f"Something went wrong code: {err.response['Error']['Code']} \n message: {err.response['Error']['Message']}"
        )
        raise


def put_data(dynamodb, project_name, project_id, month, bill, table):
    table = dynamodb.Table(table)

    try:
        response = table.update_item(
            Key={
                "Project": project_name,
                "Id": project_id,
            },
            UpdateExpression="set #monthnum = :monthbill",
            ExpressionAttributeNames={"#monthnum": str(month)},
            ExpressionAttributeValues={
                ":monthbill": bill,
            },
            ReturnValues="UPDATED_NEW",
        )
    except ClientError as err:
        logger.error(
            f"Something went wrong code: {err.response['Error']['Code']} \n message: {err.response['Error']['Message']}"
        )
        raise

    logger.info(f"UPDATED: {response['ResponseMetadata']['HTTPStatusCode']}")


def get_projects_with_ids(dynamodb, table):

    projects_with_ids = []

    projects = scan_db(dynamodb, table)

    for project in projects:
        projects_with_ids.append({"Project": project["Project"], "Id": project["Id"]})

    return projects_with_ids


def scan_db(dynamodb, table, scan_kwargs=None):
    if scan_kwargs is None:
        scan_kwargs = {}

    table = dynamodb.Table(table)

    complete = False
    records = []
    while not complete:
        try:
            response = table.scan(**scan_kwargs)
        except Exception as e:
            raise Exception(f"Error quering DB: {e}")

        records.extend(response.get("Items", []))
        next_key = response.get("LastEvaluatedKey")
        scan_kwargs["ExclusiveStartKey"] = next_key

        complete = True if next_key is None else False
    return records


def make_report(s3_client, s3_bucket, s3_key, year, data, report_path):
    df = pd.DataFrame(data)

    report_file_name = (
        f"bill_report_{datetime.datetime.now().strftime('%Y-%m-%d')}.xlsx"
    )

    try:
        with pd.ExcelWriter(
            f"{report_path}/{report_file_name}", engine="xlsxwriter"
        ) as writer:
            df.to_excel(writer, sheet_name=year, index=False)
            for column in df:
                col_idx = df.columns.get_loc(column)
                writer.sheets[year].set_column(col_idx, col_idx, 15)

            workbook = writer.book
            worksheet = writer.sheets[year]
            position = 0

            for item in range(len(data)):

                chart = workbook.add_chart({"type": "column"})
                chart.add_series(
                    {
                        "categories": [f"{year}", 0, 2, 0, 13],
                        "values": [f"{year}", 1 + item, 2, 1 + item, 13],
                        "name": f"{df['Project'].values[item]}",
                        "line": {"color": "red"},
                    }
                )
                chart.set_x_axis({"name": "Month", "position_axis": "on_tick"})
                chart.set_y_axis(
                    {"name": "Price", "major_gridlines": {"visible": False}}
                )
                chart.set_legend({"position": "none"})
                worksheet.insert_chart(f"O{20 + position}", chart)
                position += 2
        try:
            s3_client.upload_file(
                f"{report_path}/{report_file_name}",
                s3_bucket,
                f"{s3_key}/{report_file_name}",
            )
            s3_url = s3_client.generate_presigned_url(
                ClientMethod="get_object",
                Params={"Bucket": s3_bucket, "Key": f"{s3_key}/{report_file_name}"},
                ExpiresIn=3600,  # one hour in seconds, increase if needed
            )
            logger.info(
                f"The file {report_file_name} has been uploaded to the s3://{s3_bucket}/{s3_key}/{report_file_name}"
            )

            return s3_url
        except Exception as e:
            logger.exception(
                f"Something went wrong with uploading file {report_file_name}: {e}"
            )

    except Exception as e:
        logger.exception(f"Something went wrong {e}")


def sort_data_by_month(data):
    sorted_data = []
    for project in data:
        project_info = {}
        bill = {}
        for k, v in project.items():
            if k == "Project" or k == "Id":
                project_info[k] = v
            else:
                bill[int(k)] = v
        bill = dict(sorted(bill.items()))
        for k, v in bill.items():
            project_info[k] = float(v)
        sorted_data.append(project_info)

    return sorted_data


def publish_text_message(client, topic_arn, subject, message):

    try:
        response = client.publish(
            TopicArn=topic_arn,
            Message=message,
            Subject=subject,
        )
        return response
    except Exception as e:
        logger.exception(f"Something went wrong {e}")


def is_what_percent_of(num_a, num_b):
    return (num_b / 100) * num_a


def compare_month(data, current_month, sns_topic_arn, sns_client, s3url):

    month_to_compare = int(current_month) - 1
    print(month_to_compare)
    try:
        for item in data:
            logger.info(f"{item['Project']}: Compare current month with previous")
            logger.info(f"{item['Project']}: Current bill - {item[current_month]}")
            logger.info(f"{item['Project']}: Previous month - {item[month_to_compare]}")
        compare = item[month_to_compare] + is_what_percent_of(
            10, item[month_to_compare]
        )
        if item[current_month] > compare:
            logger.info(
                f"{item['Project']}: The bill is grew more than 10% compared with previous month"
            )
            if sns_topic_arn:
                publish_text_message(
                    sns_client,
                    sns_topic_arn,
                    f"The Bill for the {item['Project']} project has grown.",
                    f"""The Bill for the {item['Project']} project has grown more than 10% compared with previous month.\n
                    Current bill - {item[current_month]}, Previous month - {item[month_to_compare]}.\n
                    Please check the report via {s3url}"""
                )
        else:
            logger.info(
                f"{item['Project']}: The bill is less than 10% compared with previous month"
            )
    except Exception as e:
        logger.exception(f"Something went wrong {e}")


def main(table_name):

    logger.info("Application started")
    args = parse_args()

    projects_with_ids = get_projects_with_ids(dynamodb_resource(), table_name)
    date_range = get_date_range(args.year, args.month)

    for project in projects_with_ids:
        ce_client = client_role(project["Id"], args.region)
        data = get_bill_by_period(
            ce_client, date_range["start"], date_range["end"], project["Project"]
        )
        bill = round(
            float(
                [
                    amount_value["Total"]["BlendedCost"]["Amount"]
                    for amount_value in data["ResultsByTime"]
                ][0]
            ),
            2,
        )
        put_data(
            dynamodb_resource(),
            project["Project"],
            project["Id"],
            args.month,
            str(bill),
            table_name,
        )

    sort_data = sort_data_by_month(scan_db(dynamodb_resource(), table_name))

    s3url = make_report(
        s3_client(),
        args.bucket_name,
        args.bucket_key,
        args.year,
        sort_data,
        args.rep_path,
    )
    compare_month(sort_data, args.month, args.sns_topic_arn, sns_client(), s3url)
    if args.sns_topic_arn:
        publish_text_message(
            sns_client(),
            args.sns_topic_arn,
            "Bill report status",
            f"The report has been created and uploaded to the s3.\n You can download it via url: {s3url}",
        )
    logger.info("Application finished")


def handler(event, context):
    args = parse_args()
    TABLE_NAME = f"{args.table_name}-{args.year}"
    exist_table = check_table_exists(dynamodb_resource(), TABLE_NAME)
    if not exist_table:
        create_table(dynamodb_resource(), TABLE_NAME)
        logger.info("The table has been created")
        exit()
    if exist_table:
        main(TABLE_NAME)


if __name__ == "__main__":
    handler("event", "context")
