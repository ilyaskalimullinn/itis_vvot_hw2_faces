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
resource "yandex_storage_bucket" "bucket_photos" {
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
  memory            = 512
  execution_timeout = "10"
  content {
    zip_filename = archive_file.face_detection_zip.output_path
  }
  service_account_id = yandex_iam_service_account.sa_homework_2.id
  environment        = { "SECRET_KEY" = yandex_iam_service_account_static_access_key.sa-static-key-queue.secret_key, "ACCESS_KEY" : yandex_iam_service_account_static_access_key.sa-static-key-queue.access_key, "QUEUE_URL" : yandex_message_queue.task_queue.id }
  mounts {
    name = "bucket_photos"
    mode = "rw"
    object_storage {
      bucket = yandex_storage_bucket.bucket_photos.bucket
    }
  }
}

resource "yandex_function_iam_binding" "face_detection_biding_iam" {
  function_id = yandex_function.face_detection_func.id
  role        = "serverless.functions.invoker"

  members = [
    "serviceAccount:${yandex_iam_service_account.sa_homework_2.id}",
  ]
}

resource "yandex_function_trigger" "face_detection_trigger" {
  name        = "vvot05-photo"
  description = "Триггер, который вызывает face detection"
  folder_id   = var.folder_id
  function {
    id                 = yandex_function.face_detection_func.id
    service_account_id = yandex_iam_service_account.sa_homework_2.id
  }
  object_storage {
    bucket_id    = yandex_storage_bucket.bucket_photos.id
    suffix       = ".jpg"
    create       = true
    update       = false
    delete       = false
    batch_cutoff = 1
  }
}

resource "yandex_resourcemanager_folder_iam_member" "sa-editor-queue" {
  folder_id = var.folder_id
  role      = "ymq.admin"
  member    = "serviceAccount:${yandex_iam_service_account.sa_homework_2.id}"
}

resource "yandex_iam_service_account_static_access_key" "sa-static-key-queue" {
  service_account_id = yandex_iam_service_account.sa_homework_2.id
  description        = "static access key for message queue"
}

resource "yandex_message_queue" "task_queue" {
  name       = "vvot05-task"
  access_key = yandex_iam_service_account_static_access_key.sa-static-key-queue.access_key
  secret_key = yandex_iam_service_account_static_access_key.sa-static-key-queue.secret_key
}
