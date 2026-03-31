resource "google_cloud_run_v2_service" "api" {
  name     = "ecoalarm-api"
  location = var.region

  template {
    containers {
      image = var.api_image
    }
  }
}
