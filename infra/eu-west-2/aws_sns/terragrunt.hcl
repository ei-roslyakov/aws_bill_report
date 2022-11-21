include {
  path = find_in_parent_folders()
}

terraform {
  source = "git::ssh://git@github.com/ei-roslyakov/terraform-modules.git//aws_sns"
}

inputs = {
  name = "su-bill-report"

  subscribers = {
    opsgenie = {
      protocol               = "email"
      endpoint               = "eugene.roslyakov@sigma.software"
      endpoint_auto_confirms = true
      raw_message_delivery   = false
    }
  }

  tags = {
    Project = "SU"
  }
}