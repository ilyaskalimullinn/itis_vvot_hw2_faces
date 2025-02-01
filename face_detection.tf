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
  environment = {
    "SECRET_KEY" = yandex_message_queue.task_queue.secret_key,
    "ACCESS_KEY" = yandex_message_queue.task_queue.access_key,
    "QUEUE_URL"  = yandex_message_queue.task_queue.id
  }
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
