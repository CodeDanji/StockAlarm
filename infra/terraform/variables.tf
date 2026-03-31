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
  default = ""
}

variable "dispatcher_internal_token" {
  type      = string
  sensitive = true
  default   = "change-me"
}

variable "database_url" {
  type      = string
  sensitive = true
  default   = "sqlite+pysqlite:///./ecoalarm.db"
}

variable "eodhd_api_key" {
  type      = string
  sensitive = true
  default   = ""
}

variable "google_client_ids" {
  type    = string
  default = ""
}

variable "jwt_secret" {
  type      = string
  sensitive = true
  default   = "dev-secret-change-in-prod"
}
