resource "aws_iam_role" "github_actions" {
  name = "${var.project_name}-${var.environment}-github-actions-role"

  assume_role_policy = templatefile("${path.root}/../../policies/github_oidc_trust_policy.json.tpl", {
    oidc_provider_arn = var.oidc_provider_arn
    github_repo       = var.github_repo
    environment       = var.environment
  })

  tags = {
    Name        = "${var.project_name}-${var.environment}-github-actions-role"
    Environment = var.environment
  }
}

resource "aws_iam_policy" "github_actions_deploy" {
  name = "${var.project_name}-${var.environment}-github-actions-deploy-policy"

  policy = templatefile("${path.root}/../../policies/github_oidc_deploy_policy.json.tpl", {
    project_name = var.project_name
    environment  = var.environment
    account_id   = var.account_id
    aws_region   = var.aws_region
  })

  tags = {
    Name        = "${var.project_name}-${var.environment}-github-actions-deploy-policy"
    Environment = var.environment
  }
}

resource "aws_iam_role_policy_attachment" "github_actions_deploy" {
  role       = aws_iam_role.github_actions.name
  policy_arn = aws_iam_policy.github_actions_deploy.arn
}

resource "aws_iam_role" "terraform_ci" {
  name = "${var.project_name}-${var.environment}-terraform-ci-role"

  assume_role_policy = templatefile("${path.root}/../../policies/github_oidc_trust_policy.json.tpl", {
    oidc_provider_arn = var.oidc_provider_arn
    github_repo       = var.github_repo
    environment       = var.environment
  })

  tags = {
    Name        = "${var.project_name}-${var.environment}-terraform-ci-role"
    Environment = var.environment
  }
}

resource "aws_iam_policy" "terraform_ci_custom" {
  name = "${var.project_name}-${var.environment}-terraform-ci-policy"

  policy = templatefile("${path.root}/../../policies/github_oidc_terraform_policy.json.tpl", {
    project_name = var.project_name
    environment  = var.environment
    account_id   = var.account_id
    aws_region   = var.aws_region
    state_bucket = var.state_bucket
    lock_table   = var.lock_table
  })

  tags = {
    Name        = "${var.project_name}-${var.environment}-terraform-ci-policy"
    Environment = var.environment
  }
}

resource "aws_iam_role_policy_attachment" "terraform_ci_custom" {
  role       = aws_iam_role.terraform_ci.name
  policy_arn = aws_iam_policy.terraform_ci_custom.arn
}

resource "aws_iam_role_policy_attachment" "terraform_ci_poweruser" {
  role       = aws_iam_role.terraform_ci.name
  policy_arn = "arn:aws:iam::aws:policy/PowerUserAccess"
}
