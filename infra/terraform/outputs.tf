output "api_service_name" {
  value = google_cloud_run_v2_service.api.name
}

output "worker_job_names" {
  value = {
    ingestor  = google_cloud_run_v2_job.ingestor.name
    evaluator = google_cloud_run_v2_job.evaluator.name
    digest    = google_cloud_run_v2_job.digest.name
  }
}

output "pubsub_topic_names" {
  value = {
    ingestion  = google_pubsub_topic.ingestion.name
    evaluation = google_pubsub_topic.evaluation.name
    digest     = google_pubsub_topic.digest.name
  }
}

output "pubsub_subscription_names" {
  value = {
    ingestion  = google_pubsub_subscription.ingestion_dispatch.name
    evaluation = google_pubsub_subscription.evaluation_dispatch.name
    digest     = google_pubsub_subscription.digest_dispatch.name
  }
}
