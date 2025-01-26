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

resource "yandex_iam_service_account" "sa_homework_2" {
  name        = "sa-homework-2"
  description = "service account for homework 2"
}

// Grant permissions
resource "yandex_resourcemanager_folder_iam_member" "sa-editor" {
  folder_id = var.folder_id
  role      = "storage.editor"
  member    = "serviceAccount:${yandex_iam_service_account.sa_homework_2.id}"
}

// Create Static Access Keys
resource "yandex_iam_service_account_static_access_key" "sa-static-key" {
  service_account_id = yandex_iam_service_account.sa_homework_2.id
  description        = "static access key for object storage"
}

// Use keys to create bucket
resource "yandex_storage_bucket" "bucket" {
  access_key = yandex_iam_service_account_static_access_key.sa-static-key.access_key
  secret_key = yandex_iam_service_account_static_access_key.sa-static-key.secret_key
  bucket     = "vvot05-photo"
}

resource "archive_file" "face_detection_zip" {
  type        = "zip"
  output_path = "face_detection.zip"
  source_dir  = "face_detection"
}

resource "yandex_function" "face_detection_func" {
  name              = "vvot05-face-detection"
  user_hash         = archive_file.face_detection_zip.output_sha256
  runtime           = "python312"
  entrypoint        = "index.handler"
  memory            = 128
  execution_timeout = "10"
  content {
    zip_filename = archive_file.face_detection_zip.output_path
  }
  service_account_id = yandex_iam_service_account.sa_homework_2.id
}
