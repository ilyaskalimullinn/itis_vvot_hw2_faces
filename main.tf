variable "cloud_id" {
  type = string
}

variable "folder_id" {
  type = string
}

terraform {
  required_providers {
    yandex = {
      source = "yandex-cloud/yandex"
    }
    telegram = {
      source = "yi-jiayu/telegram"
    }
  }
  required_version = ">= 0.13"
}

provider "yandex" {
  cloud_id                 = var.cloud_id
  folder_id                = var.folder_id
  service_account_key_file = pathexpand("~/.yc-keys/key1.json")
  zone                     = "ru-central1-d"
}

// Service account
resource "yandex_iam_service_account" "sa_homework_2" {
  name        = "sa-homework-2"
  description = "service account for homework 2"
}

// Service account permissions for storage
resource "yandex_resourcemanager_folder_iam_member" "sa-editor-storage" {
  folder_id = var.folder_id
  role      = "storage.editor"
  member    = "serviceAccount:${yandex_iam_service_account.sa_homework_2.id}"
}

// Service account permissions for task queue
resource "yandex_resourcemanager_folder_iam_member" "sa-editor-queue" {
  folder_id = var.folder_id
  role      = "ymq.admin"
  member    = "serviceAccount:${yandex_iam_service_account.sa_homework_2.id}"
}

// Service account static access key
resource "yandex_iam_service_account_static_access_key" "sa-static-key" {
  service_account_id = yandex_iam_service_account.sa_homework_2.id
  description        = "static access key for object storage"
}

resource "yandex_storage_bucket" "bucket_photos" {
  access_key = yandex_iam_service_account_static_access_key.sa-static-key.access_key
  secret_key = yandex_iam_service_account_static_access_key.sa-static-key.secret_key
  bucket     = "vvot05-photo"
}

resource "yandex_message_queue" "task_queue" {
  name       = "vvot05-task"
  access_key = yandex_iam_service_account_static_access_key.sa-static-key.access_key
  secret_key = yandex_iam_service_account_static_access_key.sa-static-key.secret_key
}
