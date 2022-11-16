include {
  path = find_in_parent_folders()
}

terraform {
  source = "git::ssh://git@github.com/ei-roslyakov/terraform-modules.git//aws_s3"
}

inputs = {
  create_bucket = true

  bucket = "su-bill-report-lambda"

  tags = {
    Project = "SU"
  }
}