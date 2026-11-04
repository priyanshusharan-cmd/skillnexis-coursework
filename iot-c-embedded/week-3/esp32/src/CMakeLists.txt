idf_component_register(
    SRCS "main.c" "oled.c" "../../common/mqtt.c" "../../common/bme280.c" "../../common/station.c"
    INCLUDE_DIRS "." "../../common" "../shim" "../../avr"
    REQUIRES esp_wifi esp_netif esp_event nvs_flash driver lwip)
