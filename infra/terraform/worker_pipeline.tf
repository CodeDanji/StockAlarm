data "google_project" "current" {
  project_id = var.project_id
}

locals {
  cloud_scheduler_service_account = "service-${data.google_project.current.number}@gcp-sa-cloudscheduler.iam.gserviceaccount.com"
}

resource "google_pubsub_topic" "ingestion" {
  name = "market-ingestion"
}

resource "google_pubsub_topic" "evaluation" {
  name = "rule-evaluation"
}

resource "google_pubsub_topic" "digest" {
  name = "morning-digest"
}

resource "google_pubsub_topic_iam_member" "scheduler_publish_ingestion" {
  topic  = google_pubsub_topic.ingestion.name
  role   = "roles/pubsub.publisher"
  member = "serviceAccount:${local.cloud_scheduler_service_account}"
}

resource "google_pubsub_topic_iam_member" "scheduler_publish_evaluation" {
  topic  = google_pubsub_topic.evaluation.name
  role   = "roles/pubsub.publisher"
  member = "serviceAccount:${local.cloud_scheduler_service_account}"
}

resource "google_pubsub_topic_iam_member" "scheduler_publish_digest" {
  topic  = google_pubsub_topic.digest.name
  role   = "roles/pubsub.publisher"
  member = "serviceAccount:${local.cloud_scheduler_service_account}"
}

resource "google_cloud_run_v2_job" "ingestor" {
  name     = "ecoalarm-ingestor"
  location = var.region

  template {
    template {
      containers {
        image = var.worker_image
      }
      max_retries = 1
      timeout     = "600s"
    }
    task_count = 1
  }
}

resource "google_cloud_run_v2_job" "evaluator" {
  name     = "ecoalarm-evaluator"
  location = var.region

  template {
    template {
      containers {
        image = var.worker_image
      }
      max_retries = 1
      timeout     = "600s"
    }
    task_count = 1
  }
}

resource "google_cloud_run_v2_job" "digest" {
  name     = "ecoalarm-digest"
  location = var.region

  template {
    template {
      containers {
        image = var.worker_image
      }
      max_retries = 1
      timeout     = "600s"
    }
    task_count = 1
  }
}

resource "google_cloud_scheduler_job" "ingest_market_hours" {
  name      = "ingest-15m-market-hours"
  schedule  = "*/15 * * * 1-5"
  time_zone = var.scheduler_time_zone

  pubsub_target {
    topic_name = google_pubsub_topic.ingestion.id
    data = base64encode(
      jsonencode(
        {
          scope    = "market_hours"
          timeframe = "15m"
        }
      )
    )
  }
}

resource "google_cloud_scheduler_job" "evaluate_market_hours" {
  name      = "evaluate-15m-market-hours"
  schedule  = "*/15 * * * 1-5"
  time_zone = var.scheduler_time_zone

  pubsub_target {
    topic_name = google_pubsub_topic.evaluation.id
    data = base64encode(
      jsonencode(
        {
          scope    = "market_hours"
          timeframe = "15m"
        }
      )
    )
  }
}

resource "google_cloud_scheduler_job" "ingest_off_hours" {
  name      = "ingest-1h-off-hours"
  schedule  = "0 * * * *"
  time_zone = var.scheduler_time_zone

  pubsub_target {
    topic_name = google_pubsub_topic.ingestion.id
    data = base64encode(
      jsonencode(
        {
          scope    = "off_hours"
          timeframe = "1h"
        }
      )
    )
  }
}

resource "google_cloud_scheduler_job" "evaluate_off_hours" {
  name      = "evaluate-1h-off-hours"
  schedule  = "0 * * * *"
  time_zone = var.scheduler_time_zone

  pubsub_target {
    topic_name = google_pubsub_topic.evaluation.id
    data = base64encode(
      jsonencode(
        {
          scope    = "off_hours"
          timeframe = "1h"
        }
      )
    )
  }
}

resource "google_cloud_scheduler_job" "morning_digest" {
  name      = "digest-morning"
  schedule  = "0 7 * * *"
  time_zone = var.scheduler_time_zone

  pubsub_target {
    topic_name = google_pubsub_topic.digest.id
    data = base64encode(
      jsonencode(
        {
          scope = "morning_digest"
        }
      )
    )
  }
}
