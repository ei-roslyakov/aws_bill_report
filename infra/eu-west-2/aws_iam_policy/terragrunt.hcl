include {
  path = find_in_parent_folders()
}

terraform {
  source = "git::ssh://git@github.com/ei-roslyakov/terraform-modules.git//aws_iam_policy"
}

inputs = {
  policies = {
    "su-bill-report-policy" = {
      name = "su-bill-report-policy"
      policy_path = "./policies/su-bill-report-policy.json"
      description = "The policy for lambda bill"
    }
  }
  tags = {
    Project = "SU"
  }
}