idf_component_register(
  SRCS "main.cc" "model_data.cc" "secure_payload.cc"
  INCLUDE_DIRS "."
  PRIV_REQUIRES esp_wifi esp_netif esp_event nvs_flash mqtt esp_adc esp_driver_gpio esp_timer mbedtls
  EMBED_TXTFILES "certs/ca.crt" "certs/device.crt" "certs/device.key")
target_compile_options(${COMPONENT_LIB} PRIVATE -Wno-missing-field-initializers)
