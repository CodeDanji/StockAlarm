variable "project_id" {
  type = string
}

variable "region" {
  type    = string
  default = "asia-northeast3"
}

variable "db_tier" {
  type    = string
  default = "db-f1-micro"
}

variable "api_image" {
  type    = string
  default = "us-docker.pkg.dev/cloudrun/container/hello"
}

variable "worker_image" {
  type    = string
  default = "us-docker.pkg.dev/cloudrun/container/hello"
}

variable "scheduler_time_zone" {
  type    = string
  default = "Asia/Seoul"
}

variable "dispatcher_push_endpoint_base" {
  type    = string
  default = "https://example.com"
}

variable "dispatcher_internal_token" {
  type      = string
  sensitive = true
  default   = "change-me"
}
