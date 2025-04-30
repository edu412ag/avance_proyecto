#!/bin/bash

BUCKET_NAME="avance-proyecto"
BACKUP_FILE="backup_$(date +%F).tar.gz"
LOG_FILE="backup.log"

echo "Iniciando respaldo..." >> $LOG_FILE
tar -czf "$BACKUP_FILE" "c/Users/LENOVO/OneDrive/Escritorio/archivo correcto mysql" >> $LOG_FILE 2>&1

if aws s3 cp "$BACKUP_FILE" s3://$BUCKET_NAME/ >> $LOG_FILE 2>&1; then
    echo "Respaldo subido exitosamente." >> $LOG_FILE
else
    echo "Error en la subida del respaldo." >> $LOG_FILE
fi
