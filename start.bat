@echo off
chcp 65001
cls
echo Установка необходимых зависимостей...

REM Проверка, добавлен ли питон в PATH и работает ли pip
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo Python не был найден в PATH. Пожалуйста, установите python и попробуйте снова
    exit /b 1
)

REM Установка необходимых зависимостей из файла requirements.txt
call pip install -r requirements.txt
call npm install ws

setlocal enabledelayedexpansion

REM Поиск текущей версии
echo Проверка наличия обновлений...
for /f "usebackq tokens=*" %%i in (`powershell -Command "Get-Content 'resources\config.json' | ConvertFrom-Json | Select-Object -ExpandProperty version"`) do (
  set version=%%i
)

REM Поиск ссылки на репо в конфиге
for /f "usebackq tokens=*" %%i in (`powershell -Command "Get-Content 'resources\config.json' | ConvertFrom-Json | Select-Object -ExpandProperty repository_url"`) do (
  set repository_url=%%i
)
REM Поиск новейшей версии
for /f "usebackq tokens=*" %%i in (`powershell -Command "try { $resp = Invoke-WebRequest -UseBasicParsing '!repository_url!'; $json = $resp.Content | ConvertFrom-Json; if ($json.PSObject.Properties.Name -contains 'message' -and $json.message -eq 'Not Found') { Write-Output 'NotFound' } else { Write-Output $json.tag_name } } catch { Write-Output 'NotFound' }"`) do (
    set latest_version=%%i
)


if "!latest_version!"=="NotFound" (
    echo Репозиторий не найден на GitHub... Продолжаю...

) else if "!version!" NEQ "!latest_version!" (
    echo Найдена более новая версия !version! ^-^> !latest_version!. Хотите установить? ^(Y/N^)
    choice /c YN /n /m ""
    if errorlevel 2 (
        echo Вы отказались от установки обновления. Пропускаю...
    ) else (
        echo Вы выбрали установить обновление. Запускаю процесс обновления...
        set temp_dir=%TEMP%\%repo_name%_update
        set download_zip=!temp_dir!\update.zip
        for /f "usebackq tokens=*" %%i in (`powershell -Command "(Invoke-WebRequest -UseBasicParsing '!repository_url!').Content | ConvertFrom-Json | Select-Object -ExpandProperty assets | ForEach-Object { $_.browser_download_url } | Select-Object -First 1"` ) do (
            set download_url=%%i
        )

        mkdir "!temp_dir!" 2>nul

        echo Скачивание обновления...
        powershell -Command "Invoke-WebRequest -Uri '!download_url!' -OutFile '!download_zip!'"

        echo Распаковка обновления...
        powershell -Command "Add-Type -A

        echo Обновление файлов программы...
        for /f "delims=" %%F in ('dir /b /s "!temp_dir!"') do (
            set "file=%%F"
            echo !file! | findstr /i "resources\\config.json" >nul
            if errorlevel 1 (
                copy /y "%%F" ".\%%~nxF" >nul
            )
        )
        rd /s /q "!temp_dir!"
        echo Обновление завершено!
    )
) else (
    echo Установленная версия соответствует актуальной версии...
)
cls

call python main.py

pause