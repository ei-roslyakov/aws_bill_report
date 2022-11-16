include {
  path = find_in_parent_folders()
}

terraform {
  source = "git::ssh://git@github.com/terraform-aws-modules/terraform-aws-lambda"
}

dependency "ecr" {
  config_path = "../aws_ecr"
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
  image_uri      = format("%s%s", dependency.ecr.outputs.ecr_repository_url_map["su-bill-report"] ,"latest") 

  package_type   = "Image"
  architectures  = ["x86_64"]

  attach_policies    = true
  number_of_policies = 1
  policies           = [lookup(dependency.policy.outputs.policy_name_with_arn, "su-bill-report-policy")]
}