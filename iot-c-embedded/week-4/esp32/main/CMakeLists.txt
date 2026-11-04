idf_component_register(
    SRCS "main.c" "hal_esp32.c"
         "../../app/app.c" "../../common/agri.c"
         "../../../week-3/common/mqtt.c" "../../../week-3/common/bme280.c" "../../../week-3/esp32/src/oled.c"
    INCLUDE_DIRS "." "../../app" "../../common" "../../../week-3/common" "../../../week-3/esp32/src"
                 "../../../week-3/esp32/shim" "../../../week-3/avr"
    REQUIRES esp_wifi esp_netif esp_event nvs_flash driver esp_adc esp_https_ota app_update mbedtls lwip)
# app.c includes "FreeRTOS.h" etc. without the freertos/ prefix, as on every other FreeRTOS port
idf_build_get_property(idf_path IDF_PATH)
target_include_directories(${COMPONENT_LIB} PRIVATE "${idf_path}/components/freertos/FreeRTOS-Kernel/include/freertos")
