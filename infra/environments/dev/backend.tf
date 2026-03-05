terraform {
  backend "s3" {
    bucket         = "nbajinni-terraform-state"
    key            = "environments/dev/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "nbajinni-terraform-locks"
    encrypt        = true
  }
}
