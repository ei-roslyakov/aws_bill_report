include {
  path = find_in_parent_folders()
}

terraform {
  source = "git::ssh://git@github.com/ei-roslyakov/terraform-modules.git//aws_iam_role"
}

dependencies {
  paths = ["../aws_iam_policy"]
}

dependency "policy" {
  config_path = "../aws_iam_policy"
}

inputs = {
  roles = {
    "su-bill-report-role" = {
      name = "su-bill-report-role"
      policy_arns = [
        lookup(dependency.policy.outputs.policy_name_with_arn, "su-bill-report-policy")
      ]
      instance_profile_enable = false
    }
  }
  tags = {
    Project = "SU"
  }
}