![workflow](https://github.com/ei-roslyakov/get_bill_data/actions/workflows/tests.yml/badge.svg)
## Script for getting billing data from AWS Cost Explorer  
## How to use  
### Install dependencies

```python
pip3 install -r requirements.txt 
```
### To use AWS profile (profile must be configured, this option is only available with console report )
```python
python3 ./get_bill.py --profile=rei-prod --month=06 --year=2022 --report-to-console --no-report-to-file
```

### To make report and write it to the exel file
#### This is the default behavior, the application will read information from an excel file in the folder _report_ (first two columns) and request billing data from AWS
```python
python3 ./get_bill.py --month=06 --year=2022
```
#### this command will add a new column for each project with date and amount

### !!! Make sure that you have created a report file with projects and account ids (you can copy the template file), this file uses as source data.

### Script arguments
| Name         | Description                                       | Default    |
|--------------|---------------------------------------------------|------------|
| `--profile`  | AWS profile to get access to the Cost Explorer    | default    |
| `--month`    | The report will be created for this month         | 01    |
| `--year`     | The report will be created for this year          | 2022 |
| `--report-to-file`   | If true, will create exel report in folder report | True      |
| `--report-to-console`   | If true, will print report to console             | False      |


### Exel output example
![report](/files/report.jpg "report")
### Console output example
```
+-------------+-----------------------+--------+------+
| ProjectName | TimePeriod            | Amount | Unit |
+-------------+-----------------------+--------+------+
| rei-prod    | 2022:05:01-2022:06:01 | 5.69   | USD  |
+-------------+-----------------------+--------+------+

+-------------------------------------+-------+------+-------------------------+
| Service                             | Total | Unit | TimePeriod              |
+-------------------------------------+-------+------+-------------------------+
| AWS Key Management Service          | 0.0   | USD  | 2022-05-01 - 2022-06-01 |
| Amazon EC2 Container Registry (ECR) | 0.0   | USD  | 2022-05-01 - 2022-06-01 |
| Amazon Elastic Load Balancing       | 4.37  | USD  | 2022-05-01 - 2022-06-01 |
| Amazon Route 53                     | 1.01  | USD  | 2022-05-01 - 2022-06-01 |
| Amazon Simple Storage Service       | 0.32  | USD  | 2022-05-01 - 2022-06-01 |
| AmazonCloudWatch                    | 0.0   | USD  | 2022-05-01 - 2022-06-01 |
| Tax                                 | 0.0   | USD  | 2022-05-01 - 2022-06-01 |
+-------------------------------------+-------+------+-------------------------+
```