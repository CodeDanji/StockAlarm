data "google_project" "current" {
  project_id = var.project_id
}

locals {
  cloud_scheduler_service_account = "service-${data.google_project.current.number}@gcp-sa-cloudscheduler.iam.gserviceaccount.com"
  cloud_pubsub_service_account    = "service-${data.google_project.current.number}@gcp-sa-pubsub.iam.gserviceaccount.com"
  dispatcher_endpoint_base        = trimsuffix(var.dispatcher_push_endpoint_base, "/")
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

resource "google_service_account" "pubsub_push_dispatcher" {
  account_id   = "ecoalarm-pubsub-push"
  display_name = "EcoAlarm PubSub Push Dispatcher"
}

resource "google_service_account_iam_member" "pubsub_can_sign_oidc" {
  service_account_id = google_service_account.pubsub_push_dispatcher.name
  role               = "roles/iam.serviceAccountTokenCreator"
  member             = "serviceAccount:${local.cloud_pubsub_service_account}"
}

resource "google_cloud_run_v2_service_iam_member" "pubsub_push_invoker" {
  location = var.region
  name     = google_cloud_run_v2_service.api.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.pubsub_push_dispatcher.email}"
}

resource "google_pubsub_subscription" "ingestion_dispatch" {
  name  = "market-ingestion-dispatch"
  topic = google_pubsub_topic.ingestion.id

  push_config {
    push_endpoint = "${local.dispatcher_endpoint_base}/internal/dispatch/ingestor?token=${urlencode(var.dispatcher_internal_token)}"

    oidc_token {
      service_account_email = google_service_account.pubsub_push_dispatcher.email
      audience              = local.dispatcher_endpoint_base
    }
  }
}

resource "google_pubsub_subscription" "evaluation_dispatch" {
  name  = "rule-evaluation-dispatch"
  topic = google_pubsub_topic.evaluation.id

  push_config {
    push_endpoint = "${local.dispatcher_endpoint_base}/internal/dispatch/evaluator?token=${urlencode(var.dispatcher_internal_token)}"

    oidc_token {
      service_account_email = google_service_account.pubsub_push_dispatcher.email
      audience              = local.dispatcher_endpoint_base
    }
  }
}

resource "google_pubsub_subscription" "digest_dispatch" {
  name  = "morning-digest-dispatch"
  topic = google_pubsub_topic.digest.id

  push_config {
    push_endpoint = "${local.dispatcher_endpoint_base}/internal/dispatch/digest?token=${urlencode(var.dispatcher_internal_token)}"

    oidc_token {
      service_account_email = google_service_account.pubsub_push_dispatcher.email
      audience              = local.dispatcher_endpoint_base
    }
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
