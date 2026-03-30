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
