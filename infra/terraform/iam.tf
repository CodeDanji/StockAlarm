resource "google_service_account" "api_runtime" {
  account_id   = "ecoalarm-api-runtime"
  display_name = "EcoAlarm API Runtime"
}

resource "google_service_account" "worker_runtime" {
  account_id   = "ecoalarm-worker-runtime"
  display_name = "EcoAlarm Worker Runtime"
}

resource "google_project_iam_member" "api_runtime_run_jobs" {
  project = var.project_id
  role    = "roles/run.developer"
  member  = "serviceAccount:${google_service_account.api_runtime.email}"
}

resource "google_service_account_iam_member" "api_runtime_act_as_worker" {
  service_account_id = google_service_account.worker_runtime.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.api_runtime.email}"
}
