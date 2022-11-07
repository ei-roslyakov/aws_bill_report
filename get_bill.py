import argparse
import os.path

import boto3

from botocore.exceptions import ClientError

import loguru

import pandas as pd

logger = loguru.logger


REPORT_FILE_NAME = "report"


def parse_args():
    parsers = argparse.ArgumentParser()

    parsers.add_argument(
        "--profile",
        required=False,
        type=str,
        default="default",
        action="store",
        help="AWS Profile",
    )
    parsers.add_argument(
        "--region",
        required=False,
        type=str,
        default="eu-west-2",
        action="store",
        help="AWS region",
    )
    parsers.add_argument(
        "--month", required=False, type=str, default="01", action="store", help="Month"
    )
    parsers.add_argument(
        "--year",
        required=False,
        type=str,
        default="2022",
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

    def check_month(month):
        if month == "11" or month == "12":
            return ""
        else:
            return "0"

    suitable_value_for_month = [
        "01",
        "02",
        "03",
        "04",
        "05",
        "06",
        "07",
        "08",
        "09",
        "10",
        "11",
        "12",
    ]

    if month not in suitable_value_for_month:
        logger.exception(
            f"You have provided the wrong month number {month}, available values are {suitable_value_for_month} "
        )
        exit(1)

    if month == "01":
        start = f"{int(year) - 1}-12-01"
        end = f"{year}-{month}-01"

        return {"start": start, "end": end}

    if month != "01":
        start = f"{year}-{check_month(month)}{int(month)}-01"
        end = f"{year}-{check_month(month)}{int(month) + 1}-01"

        return {"start": start, "end": end}


def make_report(year: str, month: str, region: str):
    def sort_data_by_month(data):
        sorted_data = []
        for project in data:
            project_with_acc = dict(list(project.items())[:2])
            sorted_bill_by_month = {
                k: dict(list(project.items())[2:])[k]
                for k in sorted(dict(list(project.items())[2:]))
            }
            data = {**project_with_acc, **sorted_bill_by_month}
            sorted_data.append(data)
        return sorted_data

    date_range = get_date_range(year, month)

    df = pd.read_excel(f"report/{REPORT_FILE_NAME}.xlsx")

    data_to_write = []
    for item in df.to_dict("records"):
        try:
            ce_client = client_role(item["AccountID"], region)
            data = get_bill_by_period(
                ce_client, date_range["start"], date_range["end"], item["AccountName"]
            )
            for amount_value in data["ResultsByTime"]:
                item[f"{month}.{year}"] = round(
                    float(amount_value["Total"]["BlendedCost"]["Amount"]), 2
                )
                data_to_write.append(item)
        except ClientError as e:
            logger.exception(f"Something went wrong {e.response['Error']['Message']}")
        except Exception as e:
            logger.exception(f"Something went wrong {e}")

    df = pd.DataFrame(sort_data_by_month(data_to_write))

    try:
        logger.info("Making file backup")
        os.rename(
            f"report/{REPORT_FILE_NAME}.xlsx", f"report/{REPORT_FILE_NAME}-backup.xlsx"
        )
        with pd.ExcelWriter(
            f"report/{REPORT_FILE_NAME}.xlsx", engine="xlsxwriter"
        ) as writer:
            df.to_excel(writer, sheet_name=year, index=False)
            for column in df:
                column_width = (
                    max(df[column].astype(str).map(len).max(), len(column)) + 3
                )
                col_idx = df.columns.get_loc(column)
                writer.sheets[f"{year}"].set_column(col_idx, col_idx, column_width)

            workbook = writer.book
            worksheet = writer.sheets[year]
            position = 0

            for item in range(len(data_to_write)):
                chart = workbook.add_chart({"type": "line"})
                chart.add_series(
                    {
                        "categories": [f"{year}", 0, 2, 0, 15],
                        "values": [f"{year}", 1 + item, 2, 1 + item, 15],
                        "name": f"{df['AccountName'].values[item]}",
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

    except Exception as e:
        logger.exception(f"Something went wrong {e}")


def main():

    logger.info("Application started")
    args = parse_args()

    make_report(args.year, args.month, args.region)

    logger.info("Application finished")


if __name__ == "__main__":
    main()
