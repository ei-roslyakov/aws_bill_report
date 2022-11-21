include {
  path = find_in_parent_folders()
}

terraform {
  source = "git::ssh://git@github.com/terraform-aws-modules/terraform-aws-lambda"
}

dependencies {
  paths = ["../aws_ecr", "../aws_sns", "../aws_iam_policy"]
}

dependency "ecr" {
  config_path = "../aws_ecr"
}

dependency "sns" {
  config_path = "../aws_sns"
}

dependency "policy" {
  config_path = "../aws_iam_policy"
}

inputs = {
  function_name = "su-bill-report-lambda"
  description   = "The lambda to get bill data"
  handler       = "lambda_function.main"
  runtime       = "python3.8"

  memory_size = "1024"
  timeout     = "60"

  create_package = false
  ignore_source_code_hash = true
  image_uri      = format("%s%s", dependency.ecr.outputs.ecr_repository_url_map["su-bill-report"] ,":latest") 

  package_type   = "Image"
  architectures  = ["x86_64"]

  attach_policies    = true
  number_of_policies = 1
  policies           = [lookup(dependency.policy.outputs.policy_name_with_arn, "su-bill-report-policy")]

  environment_variables = {
    SNS_TOPIC_ARN   = dependency.sns.outputs.sns_topic["arn"],
    S3_BUCKET_NAME  = "su-bill-report",
    S3_BUCKET_KEY   = "bill-report"
  }
}