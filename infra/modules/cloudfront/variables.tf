variable "environment" {
  description = "Deployment environment (dev, prod)"
  type        = string
}

variable "project_name" {
  description = "Name of the project, used for resource naming and tagging"
  type        = string
}

variable "origins" {
  description = "One or more Origins for this distribution"
  type = list(object({
    domain_name = string
    origin_id   = string
  }))
}

variable "restrictions" {
  description = "The restriction configuration for this distribution (maximum one)."
  type = object({
    locations        = list(string)
    restriction_type = string
  })

  default = {
    locations        = []
    restriction_type = "none"
  }
}

variable "allow_methods" {
  description = "Controls which HTTP methods CloudFront processes and forwards to your Amazon S3 bucket or your custom origin."
  type        = list(string)
  default     = []
}

variable "cached_methods" {
  description = "Controls whether CloudFront caches the response to requests using the specified HTTP methods."
  type        = list(string)
  default     = []
}

variable "target_origin_id" {
  description = "Value of ID for the origin that you want CloudFront to route requests to when a request matches the path pattern either for a cache behavior or for the default cache behavior."
  type        = string
}

variable "oac_name" {
  description = "Name for the CloudFront Origin Access Control resource."
  type        = string
}

variable "distribution_name" {
  description = "Name for the CloudFront distribution resource."
  type        = string
}
