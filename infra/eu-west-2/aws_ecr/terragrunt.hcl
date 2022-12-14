include {
  path = find_in_parent_folders()
}

terraform {
  source = "git::ssh://git@github.com/ei-roslyakov/terraform-modules.git//aws_ecr"
}

inputs = {
  image_names = [
    "su-bill-report",
  ]

  image_tag_mutability = "MUTABLE"

  tags = {
    Project = "SU"
  }
}