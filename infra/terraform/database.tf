resource "google_sql_database_instance" "postgres" {
  name             = "ecoalarm-postgres"
  database_version = "POSTGRES_15"
  region           = var.region

  settings {
    tier = var.db_tier
  }
}
