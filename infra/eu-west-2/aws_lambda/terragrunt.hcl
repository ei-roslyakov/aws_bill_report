include {
  path = find_in_parent_folders()
}

terraform {
  source = "git::ssh://git@github.com/terraform-aws-modules/terraform-aws-lambda"
}

dependency "s3" {
  config_path = "../aws_s3"
}


inputs = {
  function_name = "su-bill-report-lambda"
  description   = "The lambda to get bill data "
  handler       = "lambda_function.main"
  runtime       = "python3.8"

  create_package = false
  s3_existing_package = {
    bucket = dependency.s3.outputs.s3_bucket_id[0]
    key    = "lambda/su-bill-report-lambda.zip"
  }
}