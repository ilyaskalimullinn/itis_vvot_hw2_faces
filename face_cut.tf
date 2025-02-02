resource "archive_file" "face_cut_zip" {
  type        = "zip"
  output_path = "face_cut.zip"
  source_dir  = "face_cut"
}

resource "yandex_function" "face_cut_func" {
  name              = "vvot05-face-cut"
  user_hash         = archive_file.face_cut_zip.output_sha256
  runtime           = "python312"
  entrypoint        = "index.handler"
  memory            = 128
  execution_timeout = "10"
  content {
    zip_filename = archive_file.face_cut_zip.output_path
  }
  service_account_id = yandex_iam_service_account.sa_homework_2.id
  mounts {
    name = "bucket_photos"
    mode = "rw"
    object_storage {
      bucket = yandex_storage_bucket.bucket_photos.bucket
    }
  }
  environment = {
    "SECRET_KEY"   = yandex_message_queue.task_queue.secret_key,
    "ACCESS_KEY"   = yandex_message_queue.task_queue.access_key,
    "BUCKET_FACES" = yandex_storage_bucket.bucket_faces.id
  }
}

resource "yandex_function_iam_binding" "face_cut_biding_iam" {
  function_id = yandex_function.face_cut_func.id
  role        = "serverless.functions.invoker"

  members = [
    "serviceAccount:${yandex_iam_service_account.sa_homework_2.id}",
  ]
}

resource "yandex_function_trigger" "face_cut_trigger" {
  name        = "vvot05-task"
  description = "Триггер, который вызывает face cut"
  folder_id   = var.folder_id
  function {
    id                 = yandex_function.face_cut_func.id
    service_account_id = yandex_iam_service_account.sa_homework_2.id
  }
  message_queue {
    queue_id           = yandex_message_queue.task_queue.arn
    service_account_id = yandex_iam_service_account.sa_homework_2.id
    batch_cutoff       = 1
    batch_size         = 1
  }
}
