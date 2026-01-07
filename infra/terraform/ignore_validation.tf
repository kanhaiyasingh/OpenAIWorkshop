resource "azurerm_cognitive_deployment" "gpt" {
  count                = var.create_openai_deployment ? 1 : 0
  cognitive_account_id = azurerm_ai_services.ai_hub.id
  name                 = var.openai_deployment_name

  model {
    format  = "OpenAI"
    name    = var.openai_model_name
    version = var.openai_model_version
  }

  sku {
    capacity = var.openai_deployment_capacity
    name     = "GlobalStandard"
  }
}