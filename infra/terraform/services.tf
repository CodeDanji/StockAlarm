resource "google_cloud_run_v2_service" "api" {
  name     = "ecoalarm-api"
  location = var.region

  template {
    service_account = google_service_account.api_runtime.email

    containers {
      image = var.api_image

      env {
        name  = "GCP_PROJECT_ID"
        value = var.project_id
      }

      env {
        name  = "GCP_REGION"
        value = var.region
      }

      env {
        name  = "INTERNAL_DISPATCH_TOKEN"
        value = var.dispatcher_internal_token
      }

      env {
        name  = "GOOGLE_CLIENT_IDS"
        value = var.google_client_ids
      }

      env {
        name  = "JWT_SECRET"
        value = var.jwt_secret
      }
    }
  }
}
