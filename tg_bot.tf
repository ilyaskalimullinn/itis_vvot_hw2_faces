variable "tg_bot_key" {
  type        = string
  description = "Telegram Bot Key"
  sensitive   = true
}

provider "telegram" {
  bot_token = var.tg_bot_key
}

resource "telegram_bot_webhook" "tg_webhook" {
  url = "https://api.telegram.org/bot${var.tg_bot_key}/setWebhook?url=https://functions.yandexcloud.net/${yandex_function.tg_bot_func.id}"
}

resource "archive_file" "tg_bot_zip" {
  type        = "zip"
  output_path = "tg_bot.zip"
  source_dir  = "tg_bot"
}

resource "yandex_function" "tg_bot_func" {
  name              = "vvot05-2024-boot"
  user_hash         = archive_file.tg_bot_zip.output_sha256
  runtime           = "python312"
  entrypoint        = "index.handler"
  memory            = 512
  execution_timeout = "10"
  content {
    zip_filename = archive_file.tg_bot_zip.output_path
  }
  service_account_id = yandex_iam_service_account.sa_homework_2.id
  environment = {
    "TELEGRAM_BOT_TOKEN" = var.tg_bot_key,
    "API_GATEWAY_URL"    = yandex_api_gateway.faces_api_gateway.domain
  }
  mounts {
    name = "bucket_photos"
    mode = "rw"
    object_storage {
      bucket = yandex_storage_bucket.bucket_photos.bucket
    }
  }
  mounts {
    name = "bucket_faces"
    mode = "rw"
    object_storage {
      bucket = yandex_storage_bucket.bucket_faces.bucket
    }
  }
}

resource "yandex_function_iam_binding" "tg_bot_biding_iam" {
  function_id = yandex_function.tg_bot_func.id
  role        = "serverless.functions.invoker"

  members = [
    "system:allUsers",
  ]
}
